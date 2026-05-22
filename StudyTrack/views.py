import json
import logging
from decimal import Decimal
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import GradeEntryForm, GoalForm, ProfileManagementForm, StudentRegistrationForm
from .models import GradeEntry, Goal, Notification, StudentProfile, Subject


def _normalize_subject_name(name):
	return ' '.join(name.strip().split())


def _get_or_create_subject(user, subject_name):
	normalized_name = _normalize_subject_name(subject_name)
	subject = Subject.objects.filter(user=user, name__iexact=normalized_name).first()
	if subject is None:
		subject = Subject.objects.create(user=user, name=normalized_name)
	elif subject.name != normalized_name:
		subject.name = normalized_name
		subject.save(update_fields=['name'])
	return subject


def _get_period_choices(user):
	"""Get grading period choices based on user's grading structure."""
	profile, _ = StudentProfile.objects.get_or_create(user=user)
	if profile.grading_structure == StudentProfile.TRIMESTER:
		return GradeEntry.TRIMESTER_PERIOD_CHOICES
	else:
		return GradeEntry.SEMESTER_PERIOD_CHOICES


def _academic_standing(average):
	if average is None:
		return 'No grades yet'
	if average >= 90:
		return 'Excellent'
	if average >= 85:
		return 'Very Good'
	if average >= 80:
		return 'Good'
	if average >= 75:
		return 'Fair'
	return 'Needs Improvement'


def _calculate_ched_weighted_average(subject):
	"""Calculate average for a subject - simple average since teachers handle component weighting."""
	grades = subject.grades.all()
	if not grades:
		return None

	# Group by grading period and calculate simple averages
	period_averages = {}
	for period in GradeEntry.PERIOD_CHOICES:
		period_code = period[0]
		period_grades = grades.filter(grading_period=period_code)
		if not period_grades:
			continue

		# Simple average of grades in this period
		total_sum = sum(float(grade.grade) for grade in period_grades)
		period_averages[period_code] = total_sum / len(period_grades)

	# Calculate overall average across all periods
	if period_averages:
		return round(sum(period_averages.values()) / len(period_averages), 2)
	return None


def _calculate_predictive_grade(subject, goal):
	"""
	Return predictive information for the subject and goal.

	Returned dict keys:
	  - required: float | None -> required average across remaining periods
	  - status: 'met'|'ontrack'|'achievable'|'impossible'|'no_remaining'
	  - message: string message for UI/notifications
	"""
	# Effective target: must be at least passing (75)
	effective_target = 75.0
	if goal is not None:
		try:
			effective_target = max(75.0, float(goal.target_grade))
		except Exception:
			effective_target = 75.0

	# Determine grading periods
	period_choices = _get_period_choices(subject.user)
	periods = [choice[0] for choice in period_choices]
	total_periods = len(periods)

	# Build per-period averages
	grades = subject.grades.all()
	period_averages = {}
	for period_code in periods:
		period_grades = grades.filter(grading_period=period_code)
		if not period_grades:
			continue
		total = sum(float(g.grade) for g in period_grades)
		period_averages[period_code] = total / len(period_grades)

	completed_periods = len(period_averages)
	remaining_periods = total_periods - completed_periods

	# No remaining periods
	if remaining_periods <= 0:
		current_overall = round(sum(period_averages.values()) / completed_periods, 2) if completed_periods else None
		if current_overall is None:
			return {'required': None, 'status': 'no_remaining', 'message': None}
		if current_overall >= effective_target:
			return {'required': None, 'status': 'met', 'message': 'Target already achieved.'}
		return {'required': None, 'status': 'no_remaining', 'message': 'No remaining assessments to change the outcome.'}

	# Sum current period averages
	current_sum = sum(period_averages.values())

	# required average in remaining periods so overall >= effective_target
	required_avg = (effective_target * total_periods - current_sum) / remaining_periods

	if required_avg <= 0:
		return {'required': None, 'status': 'met', 'message': 'Target already achieved.'}

	required_avg = round(required_avg, 2)

	if required_avg > 100:
		return {
			'required': required_avg,
			'status': 'impossible',
			'message': 'Target is no longer achievable. Suggest: Adjust goal. Aim for passing instead.'
		}

	if required_avg < 75:
		return {
			'required': required_avg,
			'status': 'ontrack',
			'message': 'You are on track to pass.'
		}

	return {
		'required': required_avg,
		'status': 'achievable',
		'message': f'You need an average of {required_avg} in remaining assessments to reach your target.'
	}


def _create_enhanced_grade_notifications(user, subject, grade_value, goal=None):
	"""Create intelligent notifications based on grades and goals."""
	notifications_created = []
	logger = logging.getLogger(__name__)

	# Check against target goal
	if goal and float(grade_value) < float(goal.target_grade):
		msg = (
			f'Your {subject.name} grade of {grade_value} is below your target '
			f'of {goal.target_grade}.'
		)
		notif = Notification.objects.create(user=user, message=msg)
		notifications_created.append(notif)
		logger.info('Created below-target notification for user=%s subject=%s grade=%s target=%s', user.pk, subject.pk, grade_value, goal.target_grade)

	# Check against passing threshold
	if float(grade_value) < 75:
		msg = (
			f'Alert: Your {subject.name} grade of {grade_value} is below the '
			f'passing threshold (75). Consider requesting extra support.'
		)
		notif = Notification.objects.create(user=user, message=msg)
		notifications_created.append(notif)
		logger.info('Created below-passing notification for user=%s subject=%s grade=%s', user.pk, subject.pk, grade_value)

	# Predictive notification if goal exists
	if goal:
		info = _calculate_predictive_grade(subject, goal)
		req = None
		if isinstance(info, dict):
			req = info.get('required')
		else:
			req = info

		if req and req > 90:
			msg = (
				f'Heads up: To achieve your target of {goal.target_grade} in {subject.name}, '
				f'you\'ll need an average of {req} in remaining assessments.'
			)
			notif = Notification.objects.create(user=user, message=msg)
			notifications_created.append(notif)
			logger.info('Created predictive notification for user=%s subject=%s req=%s', user.pk, subject.pk, req)

		# If impossible according to predictive calculation, create a helpful notification
		if isinstance(info, dict) and info.get('status') == 'impossible':
			notif = Notification.objects.create(user=user, message=info.get('message'))
			notifications_created.append(notif)
			logger.info('Created impossible-target notification for user=%s subject=%s', user.pk, subject.pk)

	return notifications_created


def home(request):
	if request.user.is_authenticated:
		return redirect('dashboard')
	return redirect('login')


def register(request):
	if request.user.is_authenticated:
		return redirect('dashboard')

	if request.method == 'POST':
		form = StudentRegistrationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, 'Welcome to StudyTrack. Your account has been created successfully.')
			return redirect('dashboard')
	else:
		form = StudentRegistrationForm()

	return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
	grades = GradeEntry.objects.filter(user=request.user).select_related('subject')
	overall_average = grades.aggregate(avg=Avg('grade'))['avg']
	period_average_rows = grades.values('grading_period').annotate(avg=Avg('grade')).order_by('grading_period')

	# Build per-subject datasets for the chart. We'll show one bar per subject
	# for each grading period (e.g., Midterm, Endterm) and overlay a target line
	# showing the active goal for each subject (if any).
	period_choices = _get_period_choices(request.user)
	period_codes = [code for code, _ in period_choices]
	period_labels = [label for _, label in period_choices]

	# Subjects in alphabetical order
	subjects = list(Subject.objects.filter(user=request.user).prefetch_related('grades', 'goals').order_by('name'))
	chart_subjects = [s.name for s in subjects]

	# Build datasets: one per period containing per-subject values (or None)
	palette = ['#2563eb', '#059669', '#f97316', '#ef4444']
	datasets = []
	for idx, (code, label) in enumerate(period_choices):
		data = []
		for s in subjects:
			g = s.grades.filter(grading_period=code).order_by('-recorded_at').first()
			if g:
				try:
					data.append(round(float(g.grade), 2))
				except Exception:
					data.append(None)
			else:
				data.append(None)

		color = palette[idx % len(palette)]
		datasets.append({
			'label': label,
			'data': data,
			'backgroundColor': color,
			'borderColor': color,
		})

	# Targets per subject (active goal for that subject)
	targets = []
	for s in subjects:
		goal_obj = s.goals.filter(user=request.user, active=True).order_by('-created_at').first()
		if goal_obj:
			try:
				targets.append(round(float(goal_obj.target_grade), 2))
			except Exception:
				targets.append(None)
		else:
			targets.append(None)

	# Add a bar dataset for targets. We place targets in their own stack so
	# they appear alongside the stacked grading-period bars but not combined
	# with them. This produces grouped stacks per subject: one stack for
	# grading periods and a separate stack for targets.
	datasets.append({
		'type': 'bar',
		'label': 'Target',
		'data': targets,
		'backgroundColor': 'rgba(249,115,22,0.85)',
		'borderColor': 'rgba(249,115,22,1)',
		'stack': 'targets',
		'order': 2,
	})

	# Map active goals by subject id so other parts of the view can reference them
	goals_by_subject_id = {g.subject_id: g for g in Goal.objects.filter(user=request.user, active=True)}

	subject_summaries = []
	# Build per-subject summaries compatible with includes/subject_table.html
	for subject in Subject.objects.filter(user=request.user).prefetch_related('grades').order_by('name'):
		# Latest grade (GradeEntry ordering ensures newest first)
		latest_grade = subject.grades.first()

		# Use CHED weighted average
		subject_average = _calculate_ched_weighted_average(subject)

		goal = goals_by_subject_id.get(subject.id)
		target_progress = None
		gap = None
		prediction_info = None

		if goal and latest_grade is not None:
			try:
				gap = round(float(latest_grade.grade) - float(goal.target_grade), 2)
				if float(goal.target_grade) > 0:
					target_progress = min(round((float(latest_grade.grade) / float(goal.target_grade)) * 100, 1), 100)
			except Exception:
				gap = None
			# Get predictive info
			prediction_info = _calculate_predictive_grade(subject, goal)

		# Build ordered list of (code, label, latest_grade_obj) per period for this user
		period_grade_pairs = []
		for code, label in period_choices:
			g = subject.grades.filter(grading_period=code).order_by('-recorded_at').first()
			period_grade_pairs.append((code, label, g))

		subject_summaries.append({
			'subject': subject,
			'latest_grade': latest_grade,
			'average': subject_average,
			'goal': goal,
			'gap': gap,
			'target_progress': target_progress,
			'prediction_info': prediction_info,
			'period_grade_pairs': period_grade_pairs,
		})

	notifications = request.user.notifications.all()[:5]
	unread_count = request.user.notifications.filter(is_read=False).count()


	context = {
		'overall_average': round(float(overall_average), 2) if overall_average is not None else None,
		'standing': _academic_standing(float(overall_average)) if overall_average is not None else 'No grades yet',
		# Chart data for per-subject grouped bars and target line
		'chart_subjects_json': json.dumps(chart_subjects),
		'chart_datasets_json': json.dumps(datasets),
		'chart_period_labels_json': json.dumps(period_labels),
		'subject_summaries': subject_summaries,
		'notifications': notifications,
		'unread_count': unread_count,
		'recent_grades': grades.select_related('subject')[:10],
		'total_goals': Goal.objects.filter(user=request.user, active=True).count(),
		'total_subjects': Subject.objects.filter(user=request.user).count(),
		'period_choices': period_choices,
	}
	return render(request, 'dashboard.html', context)


@login_required
def add_grade(request):
	if request.method == 'POST':
		post_data = request.POST
		# Support legacy POSTs that send 'subject_name' (string) by converting to subject id
		if 'subject_name' in request.POST and 'subject' not in request.POST:
			subject = _get_or_create_subject(request.user, request.POST.get('subject_name'))
			post_data = request.POST.copy()
			post_data['subject'] = str(subject.pk)

		form = GradeEntryForm(post_data, user=request.user)
		if form.is_valid():
			subject = form.cleaned_data['subject']
			grade_entry = GradeEntry.objects.create(
				user=request.user,
				subject=subject,
				grading_period=form.cleaned_data['grading_period'],
				grade=form.cleaned_data['grade'],
				notes=form.cleaned_data['notes'],
			)

			# Get active goal
			active_goal = Goal.objects.filter(user=request.user, subject=subject, active=True).order_by('-created_at').first()

			messages.success(request, f'Grade for {subject.name} was saved successfully.')
			# Create notifications and inform the user immediately if any were generated
			notifs = _create_enhanced_grade_notifications(request.user, subject, grade_entry.grade, active_goal)
			if notif_count := len(notifs):
				# show a short message so the user sees something immediately
				messages.warning(request, f'{notif_count} notification(s) created related to this grade.')
			return redirect('dashboard')
	else:
		form = GradeEntryForm(user=request.user)

	return render(request, 'grade_form.html', {'form': form})


@login_required
def add_goal(request):
	if request.method == 'POST':
		form = GoalForm(request.POST)
		if form.is_valid():
			subject = _get_or_create_subject(request.user, form.cleaned_data['subject_name'])
			Goal.objects.filter(user=request.user, subject=subject, active=True).update(active=False)
			Goal.objects.create(
				user=request.user,
				subject=subject,
				target_grade=form.cleaned_data['target_grade'],
				active=form.cleaned_data['active'],
			)
			messages.success(request, f'Subject and goal for {subject.name} have been saved.')
			return redirect('dashboard')
	else:
		form = GoalForm()

	# Include an empty grade form so both forms can be shown on the same page
	grade_form = GradeEntryForm(user=request.user)

	return render(request, 'goal_form.html', {'form': form, 'grade_form': grade_form})



@login_required
def manage_profile(request):
	if request.method == 'POST':
		form = ProfileManagementForm(request.POST, user=request.user)
		if form.is_valid():
			form.save()
			messages.success(request, 'Your profile has been updated successfully.')
			return redirect('manage_profile')
	else:
		form = ProfileManagementForm(user=request.user)

	return render(request, 'profile_edit.html', {'form': form, 'username': request.user.username})



@login_required
def notifications_view(request):
	if request.method == 'POST':
		request.user.notifications.filter(is_read=False).update(is_read=True)
		messages.success(request, 'All notifications were marked as read.')
		return redirect('notifications')

	notifications = request.user.notifications.all()
	return render(request, 'notifications.html', {'notifications': notifications})


@login_required
def mark_notification_read(request, pk):
	notification = get_object_or_404(Notification, pk=pk, user=request.user)
	notification.is_read = True
	notification.save(update_fields=['is_read'])
	messages.success(request, 'Notification marked as read.')
	return redirect('notifications')


@login_required
def delete_notification(request, pk):
	"""Delete a notification belonging to the current user."""
	notification = get_object_or_404(Notification, pk=pk, user=request.user)
	if request.method == 'POST':
		notification.delete()
		messages.success(request, 'Notification deleted successfully.')
		return redirect('notifications')

	# For safety, render a simple confirmation page (re-use delete template pattern)
	return render(request, 'delete_notification.html', {'notification': notification})


@login_required
def data_management(request):
	"""Display all subjects with options to edit or delete."""
	subjects = Subject.objects.filter(user=request.user).prefetch_related('grades', 'goals').order_by('name')

	subject_data = []
	# Get period choices for this user so we can show columns for each grading period
	period_choices = _get_period_choices(request.user)
	for subject in subjects:
		grades = subject.grades.all()
		goals = subject.goals.filter(active=True)

		# Latest grade
		subject_grades = list(grades)
		latest_grade = subject_grades[0] if subject_grades else None

		# Calculate average
		if grades:
			average = sum(float(g.grade) for g in grades) / len(grades)
			average = round(average, 2)
		else:
			average = None

		# Get active goal
		goal_obj = goals.first() if goals else None
		target_grade = goal_obj.target_grade if goal_obj else None

		# Progress toward goal
		gap = None
		target_progress = None
		if goal_obj and latest_grade is not None:
			try:
				gap = round(float(latest_grade.grade) - float(goal_obj.target_grade), 2)
				if float(goal_obj.target_grade) > 0:
					target_progress = min(round((float(latest_grade.grade) / float(goal_obj.target_grade)) * 100, 1), 100)
			except Exception:
				gap = None

		# Predictive info
		prediction_info = None
		if goal_obj:
			prediction_info = _calculate_predictive_grade(subject, goal_obj)
		# Build an ordered list of (code, label, latest_grade_obj) for the user's period choices
		period_grade_pairs = []
		for code, label in period_choices:
			g = grades.filter(grading_period=code).order_by('-recorded_at').first()
			period_grade_pairs.append((code, label, g))

		subject_data.append({
			'subject': subject,
			'latest_grade': latest_grade,
			'grades_count': grades.count(),
			'average': average,
			'goal': goal_obj,
			'gap': gap,
			'target_progress': target_progress,
			'goals_count': goals.count(),
			'prediction_info': prediction_info,
			'period_grade_pairs': period_grade_pairs,
		})

	context = {
		'subject_data': subject_data,
		'total_subjects': len(subjects),
		'period_choices': period_choices,
		'grading_structure': StudentProfile.objects.get_or_create(user=request.user)[0].grading_structure,
	}
	return render(request, 'data_management.html', context)


@login_required
def edit_subject(request, pk):
	"""Edit subject name."""
	subject = get_object_or_404(Subject, pk=pk, user=request.user)

	if request.method == 'POST':
		new_name = request.POST.get('name', '').strip()
		if new_name:
			# Check if name already exists for this user
			existing = Subject.objects.filter(user=request.user, name__iexact=new_name).exclude(pk=pk).first()
			if existing:
				messages.error(request, f'A subject named "{new_name}" already exists.')
			else:
				subject.name = ' '.join(new_name.split())  # Normalize spacing
				subject.save(update_fields=['name'])
				messages.success(request, f'Subject "{subject.name}" updated successfully.')
				return redirect('data_management')
		else:
			messages.error(request, 'Subject name cannot be empty.')

	context = {'subject': subject}
	return render(request, 'edit_subject.html', context)


@login_required
def delete_subject(request, pk):
	"""Delete subject and all associated data."""
	subject = get_object_or_404(Subject, pk=pk, user=request.user)
	subject_name = subject.name

	if request.method == 'POST':
		# Delete all grades and goals associated with this subject
		subject.grades.all().delete()
		subject.goals.all().delete()
		subject.delete()
		messages.success(request, f'Subject "{subject_name}" and all associated data have been deleted.')
		return redirect('data_management')

	context = {'subject': subject}
	return render(request, 'delete_subject.html', context)


@login_required
def edit_grade(request, pk):
	grade = get_object_or_404(GradeEntry, pk=pk, user=request.user)
	if request.method == 'POST':
		# allow editing grading_period, grade, notes
		grading_period = request.POST.get('grading_period')
		grade_value = request.POST.get('grade')
		notes = request.POST.get('notes', '')
		if grading_period and grade_value is not None:
			try:
				grade.grade = Decimal(grade_value)
				grade.grading_period = grading_period
				grade.notes = notes
				grade.save(update_fields=['grade', 'grading_period', 'notes'])
				messages.success(request, 'Grade updated successfully.')
				return redirect('edit_subject', pk=grade.subject.pk)
			except Exception:
				messages.error(request, 'Invalid grade value.')

	period_choices = _get_period_choices(request.user)
	context = {'grade': grade, 'period_choices': period_choices}
	return render(request, 'edit_grade.html', context)


@login_required
def delete_grade(request, pk):
	grade = get_object_or_404(GradeEntry, pk=pk, user=request.user)
	subject_pk = grade.subject.pk
	if request.method == 'POST':
		grade.delete()
		messages.success(request, 'Grade deleted successfully.')
		return redirect('edit_subject', pk=subject_pk)
	return render(request, 'delete_grade.html', {'grade': grade})


@login_required
def edit_goal(request, pk):
	goal = get_object_or_404(Goal, pk=pk, user=request.user)
	if request.method == 'POST':
		target = request.POST.get('target_grade')
		active = request.POST.get('active') == 'on'
		try:
			goal.target_grade = Decimal(target)
			goal.active = active
			goal.save(update_fields=['target_grade', 'active'])
			messages.success(request, 'Goal updated successfully.')
			return redirect('edit_subject', pk=goal.subject.pk)
		except Exception:
			messages.error(request, 'Invalid target grade.')

	context = {'goal': goal}
	return render(request, 'edit_goal.html', context)


@login_required
def delete_goal(request, pk):
	goal = get_object_or_404(Goal, pk=pk, user=request.user)
	subject_pk = goal.subject.pk
	if request.method == 'POST':
		goal.delete()
		messages.success(request, 'Goal deleted successfully.')
		return redirect('edit_subject', pk=subject_pk)
	return render(request, 'delete_goal.html', {'goal': goal})

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


def _get_or_create_subject(user, subject_name, year, semester):
	normalized_name = _normalize_subject_name(subject_name)
	subject = Subject.objects.filter(user=user, name__iexact=normalized_name, year=year, semester=semester).first()
	if subject is None:
		subject = Subject.objects.create(user=user, name=normalized_name, year=year, semester=semester)
	elif subject.name != normalized_name:
		subject.name = normalized_name
		subject.save(update_fields=['name'])
	return subject


def _get_period_choices(user, semester=None):
	"""Get grading period choices based on user's grading structure.

	If semester is provided ('1' or '2'), use the per-semester internal structure
	configured on the user's StudentProfile. Defaults to semester 1.
	"""
	profile, _ = StudentProfile.objects.get_or_create(user=user)
	if semester == '2':
		structure = profile.sem2_grading_periods
	else:
		structure = profile.sem1_grading_periods

	if structure == StudentProfile.THREE_PERIODS:
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

	# Semester-specific period choices
	sem1_period_choices = _get_period_choices(request.user, '1')
	sem2_period_choices = _get_period_choices(request.user, '2')

	# Fetch ALL subjects for the user
	subjects = list(Subject.objects.filter(user=request.user).prefetch_related('grades', 'goals').order_by('name'))

	# Map active goals by subject id and semester so other parts of the view can reference them
	active_goals = Goal.objects.filter(user=request.user, active=True)
	goals_by_subject_sem = {(g.subject_id, g.semester): g for g in active_goals}
	
	# Total subjects (unfiltered by year) for stats if needed
	total_subjects = Subject.objects.filter(user=request.user).count()

	# Helper to build datasets for a given set of period choices and
	# targets determined by active goals for the given semester.
	palette = ['#2563eb', '#059669', '#f97316', '#ef4444']

	def build_datasets_for(period_choices_for_sem, semester_key, year_key):
		# Include all subjects for this semester and year
		subjects_for_sem = [s for s in subjects if s.semester == semester_key and s.year == year_key]
		
		# Chart subjects specific to this filtered subset
		chart_subjects_subset = [s.name for s in subjects_for_sem]
		
		ds = []
		for idx, (code, label) in enumerate(period_choices_for_sem):
			data = []
			for s in subjects_for_sem:
				g = s.grades.filter(grading_period=code).order_by('-recorded_at').first()
				if g:
					try:
						data.append(round(float(g.grade), 2))
					except Exception:
						data.append(None)
				else:
					data.append(None)

			color = palette[idx % len(palette)]
			ds.append({
				'label': label,
				'data': data,
				'backgroundColor': color,
				'borderColor': color,
			})

		# Targets per subject
		targets_sem = []
		for s in subjects_for_sem:
			# Get the active goal for the subject
			goal_obj = next((g for g in s.goals.all() if g.active), None)
			if goal_obj:
				try:
					targets_sem.append(round(float(goal_obj.target_grade), 2))
				except Exception:
					targets_sem.append(None)
			else:
				targets_sem.append(None)

		ds.append({
			'type': 'bar',
			'label': 'Target',
			'data': targets_sem,
			'backgroundColor': 'rgba(249,115,22,0.85)',
			'borderColor': 'rgba(249,115,22,1)',
			'stack': 'targets',
			'order': 2,
		})

		return {
			'subject_names': chart_subjects_subset,
			'datasets': ds
		}

	# Build time series data for Midterm/Endterm comparison charts
	def build_time_series_data(semester_key, year_key):
		"""Build chart data with Midterm Actual, Midterm Goal, Endterm Actual, Endterm Goal, and Overall Trend"""
		# Get subjects in this semester and year
		subjects_in_sem = [s for s in subjects if s.semester == semester_key and s.year == year_key]
		
		if not subjects_in_sem:
			return {'subject_names': [], 'datasets': []}
		
		subject_names = [s.name for s in subjects_in_sem]
		
		# Initialize data arrays for each metric
		midterm_actual = []
		midterm_goal = []
		endterm_actual = []
		endterm_goal = []
		overall_trend = []
		
		for subject in subjects_in_sem:
			# Get grades
			midterm_grade = subject.grades.filter(grading_period=GradeEntry.MIDTERM).order_by('-recorded_at').first()
			endterm_grade = subject.grades.filter(grading_period=GradeEntry.ENDTERM).order_by('-recorded_at').first()
			
			# Get goal for this subject
			goal = next((g for g in subject.goals.all() if g.active), None)
			
			# Midterm actual
			midterm_actual.append(float(midterm_grade.grade) if midterm_grade else None)
			
			# Midterm goal
			midterm_goal.append(float(goal.target_grade) if goal else None)
			
			# Endterm actual
			endterm_actual.append(float(endterm_grade.grade) if endterm_grade else None)
			
			# Endterm goal
			endterm_goal.append(float(goal.target_grade) if goal else None)
			
			# Overall average (calculate ched weighted if possible, else simple average)
			subject_average = _calculate_ched_weighted_average(subject)
			
			if subject_average is not None and goal is not None:
				gap = round(float(subject_average) - float(goal.target_grade), 2)
				overall_trend.append(gap)
			else:
				overall_trend.append(None)
		
		# Define colors based on positive/negative gap
		bg_colors = []
		border_colors = []
		for val in overall_trend:
			if val is None:
				bg_colors.append('rgba(156, 163, 175, 0.5)')
				border_colors.append('rgba(156, 163, 175, 1)')
			elif val >= 0:
				bg_colors.append('rgba(16, 185, 129, 0.85)') # Green
				border_colors.append('rgba(5, 150, 105, 1)')
			else:
				bg_colors.append('rgba(239, 68, 68, 0.85)') # Red
				border_colors.append('rgba(220, 38, 38, 1)')
		
		return {
			'subject_names': subject_names,
			'datasets': [
				{
					'label': 'Distance to Goal',
					'data': overall_trend,
					'backgroundColor': bg_colors,
					'borderColor': border_colors,
					'borderWidth': 1,
				}
			]
		}
	
	
	# Group everything by year and semester for independent tabs
	progress_tracking_data = {}
	goal_distance_data = {}
	subject_summaries = {}

	for year_code, year_label in Subject.YEAR_CHOICES:
		progress_tracking_data[year_code] = {
			Subject.SEM_1: build_datasets_for(sem1_period_choices, Subject.SEM_1, year_code),
			Subject.SEM_2: build_datasets_for(sem2_period_choices, Subject.SEM_2, year_code),
		}
		goal_distance_data[year_code] = {
			Subject.SEM_1: build_time_series_data(Subject.SEM_1, year_code),
			Subject.SEM_2: build_time_series_data(Subject.SEM_2, year_code),
		}
		
		# Subject summaries for this year
		summaries_sem1 = []
		summaries_sem2 = []
		
		for subject in [s for s in subjects if s.year == year_code]:
			latest_grade = subject.grades.first()
			subject_average = _calculate_ched_weighted_average(subject)

			# Active goal
			active_goal = next((g for g in subject.goals.all() if g.active), None)

			# Build ordered list of (code, label, latest_grade_obj) per period for this user
			period_grade_pairs = []
			for code, label in period_choices:
				g = subject.grades.filter(grading_period=code).order_by('-recorded_at').first()
				period_grade_pairs.append((code, label, g))

			# Determine filtering status
			status = 'no_goal'
			gap = None
			target_progress = None
			prediction_info = None

			if active_goal:
				if latest_grade is not None:
					try:
						gap = round(float(latest_grade.grade) - float(active_goal.target_grade), 2)
						if float(active_goal.target_grade) > 0:
							target_progress = min(round((float(latest_grade.grade) / float(active_goal.target_grade)) * 100, 1), 100)
					except Exception:
						gap = None
				prediction_info = _calculate_predictive_grade(subject, active_goal)
				status = 'below' if (gap is not None and gap < 0) else 'ontrack'

			subject_data = {
				'subject': subject,
				'latest_grade': latest_grade,
				'grades_count': subject.grades.count(),
				'average': subject_average,
				'goal': active_goal,
				'gap': gap,
				'target_progress': target_progress,
				'goals_count': subject.goals.filter(active=True).count(),
				'prediction_info': prediction_info,
				'period_grade_pairs': period_grade_pairs,
				'status': status,
			}

			if subject.semester == Subject.SEM_1:
				summaries_sem1.append(subject_data)
			elif subject.semester == Subject.SEM_2:
				summaries_sem2.append(subject_data)
			
		subject_summaries[year_code] = {
			Subject.SEM_1: summaries_sem1,
			Subject.SEM_2: summaries_sem2,
		}

	notifications = request.user.notifications.all()[:5]
	unread_count = request.user.notifications.filter(is_read=False).count()

	# Also prepare sem-specific labels for the toggle
	period_labels_sem1 = [label for _, label in sem1_period_choices]
	period_labels_sem2 = [label for _, label in sem2_period_choices]

	context = {
		'overall_average': round(float(overall_average), 2) if overall_average is not None else None,
		'standing': _academic_standing(float(overall_average)) if overall_average is not None else 'No grades yet',
		# Chart data for per-subject grouped bars and target line
		'progress_tracking_json': json.dumps(progress_tracking_data),
		'goal_distance_json': json.dumps(goal_distance_data),
		'chart_period_labels_json': json.dumps(period_labels),
		'chart_period_labels_sem1_json': json.dumps(period_labels_sem1),
		'chart_period_labels_sem2_json': json.dumps(period_labels_sem2),
		'sem1_period_choices': sem1_period_choices,
		'sem2_period_choices': sem2_period_choices,
		'subject_summaries': subject_summaries,
		'notifications': notifications,
		'unread_count': unread_count,
		'recent_grades': grades.select_related('subject')[:10],
		'total_goals': Goal.objects.filter(user=request.user, active=True).count(),
		'total_subjects': Subject.objects.filter(user=request.user).count(),
		'period_choices': period_choices,
		'year_choices': Subject.YEAR_CHOICES,
	}
	return render(request, 'dashboard.html', context)


@login_required
def add_grade(request):
	if request.method == 'POST':
		post_data = request.POST
		# Support legacy POSTs that send 'subject_name' (string) by converting to subject id
		if 'subject_name' in request.POST and 'subject' not in request.POST:
			year = request.POST.get('year', '1')
			semester = request.POST.get('semester', '1')
			subject = _get_or_create_subject(request.user, request.POST.get('subject_name'), year, semester)
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
			subject = _get_or_create_subject(request.user, form.cleaned_data['subject_name'], form.cleaned_data['year'], form.cleaned_data['semester'])
			Goal.objects.filter(user=request.user, subject=subject, active=True).update(active=False)
			Goal.objects.create(
				user=request.user,
				subject=subject,
				target_grade=form.cleaned_data['target_grade'],
				active=form.cleaned_data['active'],
				semester=form.cleaned_data.get('semester', Goal.FIRST_SEM),
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
	selected_year = request.GET.get('year', Subject.YEAR_1)
	if selected_year not in dict(Subject.YEAR_CHOICES):
		selected_year = Subject.YEAR_1
		
	subjects = Subject.objects.filter(user=request.user, year=selected_year).prefetch_related('grades', 'goals').order_by('name')

	# Get total subjects across all years for statistics
	total_subjects = Subject.objects.filter(user=request.user).count()

	# Prepare semester-specific subject lists
	subject_data_sem1 = []
	subject_data_sem2 = []

	# Get period choices for this user so we can show columns for each grading period
	period_choices = _get_period_choices(request.user)
	sem1_period_choices = _get_period_choices(request.user, '1')
	sem2_period_choices = _get_period_choices(request.user, '2')

	# Only include subjects in a semester list if there is an active goal for
	# that semester. Since grading period codes are shared between semesters,
	# we cannot reliably infer semester from grading_period alone.
	# The semester separation is purely based on the goal's semester assignment.

	for subject in subjects:
		grades = subject.grades.all()

		# Latest grade
		subject_grades = list(grades)
		latest_grade = subject_grades[0] if subject_grades else None

		# Calculate average
		if grades:
			average = sum(float(g.grade) for g in grades) / len(grades)
			average = round(average, 2)
		else:
			average = None

		# Get active goals per semester
		goal_obj_sem1 = subject.goals.filter(user=request.user, active=True, semester=Goal.FIRST_SEM).order_by('-created_at').first()
		goal_obj_sem2 = subject.goals.filter(user=request.user, active=True, semester=Goal.SECOND_SEM).order_by('-created_at').first()


		# Compute info for semester 1
		gap1 = None
		target_progress1 = None
		prediction_info1 = None
		if goal_obj_sem1 and latest_grade is not None:
			try:
				gap1 = round(float(latest_grade.grade) - float(goal_obj_sem1.target_grade), 2)
				if float(goal_obj_sem1.target_grade) > 0:
					target_progress1 = min(round((float(latest_grade.grade) / float(goal_obj_sem1.target_grade)) * 100, 1), 100)
			except Exception:
				gap1 = None
			prediction_info1 = _calculate_predictive_grade(subject, goal_obj_sem1)

		# Compute info for semester 2
		gap2 = None
		target_progress2 = None
		prediction_info2 = None
		if goal_obj_sem2 and latest_grade is not None:
			try:
				gap2 = round(float(latest_grade.grade) - float(goal_obj_sem2.target_grade), 2)
				if float(goal_obj_sem2.target_grade) > 0:
					target_progress2 = min(round((float(latest_grade.grade) / float(goal_obj_sem2.target_grade)) * 100, 1), 100)
			except Exception:
				gap2 = None
			prediction_info2 = _calculate_predictive_grade(subject, goal_obj_sem2)

		# Build ordered list of (code, label, latest_grade_obj) per period for this user
		period_grade_pairs = []
		for code, label in period_choices:
			g = grades.filter(grading_period=code).order_by('-recorded_at').first()
			period_grade_pairs.append((code, label, g))

		# Determine status for filtering
		status1 = 'no_goal'
		if goal_obj_sem1:
			status1 = 'below' if (gap1 is not None and gap1 < 0) else 'ontrack'

		status2 = 'no_goal'
		if goal_obj_sem2:
			status2 = 'below' if (gap2 is not None and gap2 < 0) else 'ontrack'

		# Append to sem1 list if subject is from sem 1
		if subject.semester == Subject.SEM_1:
			subject_data_sem1.append({
				'subject': subject,
				'latest_grade': latest_grade,
				'grades_count': grades.count(),
				'average': average,
				'goal': goal_obj_sem1,
				'gap': gap1,
				'target_progress': target_progress1,
				'goals_count': subject.goals.filter(active=True).count(),
				'prediction_info': prediction_info1,
				'period_grade_pairs': period_grade_pairs,
				'status': status1,
			})

		# Append to sem2 list if subject is from sem 2
		elif subject.semester == Subject.SEM_2:
			subject_data_sem2.append({
				'subject': subject,
				'latest_grade': latest_grade,
				'grades_count': grades.count(),
				'average': average,
				'goal': goal_obj_sem2,
				'gap': gap2,
				'target_progress': target_progress2,
				'goals_count': subject.goals.filter(active=True).count(),
				'prediction_info': prediction_info2,
				'period_grade_pairs': period_grade_pairs,
				'status': status2,
			})

	context = {
		'subject_data_sem1': subject_data_sem1,
		'subject_data_sem2': subject_data_sem2,
		'total_subjects': total_subjects,
		'period_choices': period_choices,
		'sem1_period_choices': sem1_period_choices,
		'sem2_period_choices': sem2_period_choices,
		'year_choices': Subject.YEAR_CHOICES,
		'selected_year': selected_year,
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


@login_required
def view_subject(request, pk):
	"""View subject details, grades, and goals."""
	subject = get_object_or_404(Subject, pk=pk, user=request.user)

	# Get all grades and goals for this subject
	grades = subject.grades.all().order_by('grading_period')
	goals = subject.goals.filter(user=request.user, active=True).order_by('semester')

	# Calculate current average based on grades
	current_average = _calculate_ched_weighted_average(subject)

	# Latest grading period for this subject (to highlight in the UI)
	latest_grading_period = grades.last().grading_period if grades.exists() else None

	# Prepare data for the time series chart (Midterm/Endterm comparison)
	# Show actual grades vs. target goals
	time_series_data = {
		'labels': [],
		'datasets': []
	}

	# Only include periods that have grades recorded
	recorded_periods = grades.values_list('grading_period', flat=True).distinct()

	# Midterm and Endterm are the only periods used for this chart
	if GradeEntry.MIDTERM in recorded_periods and GradeEntry.ENDTERM in recorded_periods:
		# Add chart data only if both Midterm and Endterm grades are present
		midterm_grade = grades.filter(grading_period=GradeEntry.MIDTERM).first()
		endterm_grade = grades.filter(grading_period=GradeEntry.ENDTERM).first()

		# Use the subject name as the label (single label for this subject)
		time_series_data['labels'].append(subject.name)

		# Actual grades dataset
		time_series_data['datasets'].append({
			'label': 'Actual Grade',
			'data': [midterm_grade.grade, endterm_grade.grade],
			'borderColor': '#2563eb',
			'backgroundColor': 'rgba(37, 99, 235, 0.1)',
			'borderWidth': 2,
			'tension': 0.3,
			'fill': False,
			'pointRadius': 5,
			'pointBackgroundColor': '#2563eb',
		})

		# Goal grades dataset (targets)
		for goal in goals:
			time_series_data['datasets'].append({
				'label': f'Goal {goal.semester}',
				'data': [goal.target_grade, goal.target_grade],
				'borderColor': '#f97316',
				'backgroundColor': 'rgba(249, 115, 22, 0.15)',
				'borderWidth': 2,
				'borderDash': [5, 5],
				'tension': 0.3,
				'fill': False,
				'pointRadius': 4,
				'pointBackgroundColor': '#f97316',
				'pointStyle': 'triangle',
			})

	# Build the time series data for this subject
	time_series_data = json.dumps(time_series_data)

	context = {
		'subject': subject,
		'grades': grades,
		'goals': goals,
		'current_average': current_average,
		'latest_grading_period': latest_grading_period,
		'time_series_data': time_series_data,
	}

	return render(request, 'view_subject.html', context)



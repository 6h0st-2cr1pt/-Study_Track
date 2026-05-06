import json
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
	Calculate the minimum grade needed in remaining terms to achieve target.
	Returns None if target is already achieved or no grades exist.
	"""
	all_grades = list(subject.grades.all())
	if not all_grades:
		return None

	# Calculate current average
	current_avg = _calculate_ched_weighted_average(subject)
	if current_avg is None:
		return None

	target = float(goal.target_grade)

	# If already achieved target, return None
	if current_avg >= target:
		return None

	# Get correct periods based on user's grading structure
	period_choices = _get_period_choices(subject.user)
	periods = [choice[0] for choice in period_choices]
	entries_by_period = defaultdict(list)

	for grade in all_grades:
		entries_by_period[grade.grading_period].append(grade)

	# Count completed periods and calculate what's needed
	completed_periods = len(entries_by_period)
	remaining_periods = len(periods) - completed_periods

	if remaining_periods <= 0:
		return None

	# Calculate minimum required average in remaining periods
	# Formula: (target * total_periods - current_sum) / remaining_periods
	current_sum = current_avg * completed_periods
	required_avg = (target * len(periods) - current_sum) / remaining_periods

	return max(0, min(100, round(required_avg, 2)))


def _create_enhanced_grade_notifications(user, subject, grade_value, goal=None):
	"""Create intelligent notifications based on grades and goals."""
	notifications_created = []

	# Check against target goal
	if goal and float(grade_value) < float(goal.target_grade):
		msg = (
			f'Your {subject.name} grade of {grade_value} is below your target '
			f'of {goal.target_grade}.'
		)
		notif = Notification.objects.create(user=user, message=msg)
		notifications_created.append(notif)

	# Check against passing threshold
	if float(grade_value) < 75:
		msg = (
			f'Alert: Your {subject.name} grade of {grade_value} is below the '
			f'passing threshold (75). Consider requesting extra support.'
		)
		notif = Notification.objects.create(user=user, message=msg)
		notifications_created.append(notif)

	# Predictive notification if goal exists
	if goal:
		required = _calculate_predictive_grade(subject, goal)
		if required and required > 90:
			msg = (
				f'Heads up: To achieve your target of {goal.target_grade} in {subject.name}, '
				f'you\'ll need an average of {required} in remaining assessments.'
			)
			notif = Notification.objects.create(user=user, message=msg)
			notifications_created.append(notif)

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

	# Get correct period choices based on user's grading structure
	period_choices = _get_period_choices(request.user)
	chart_labels = [label for _, label in period_choices]
	period_map = {choice: 0.0 for choice, _ in period_choices}
	for row in period_average_rows:
		period_map[row['grading_period']] = round(float(row['avg']), 2)
	chart_data = [period_map[choice] for choice, _ in period_choices]

	goals = Goal.objects.filter(user=request.user, active=True).select_related('subject')
	goals_by_subject_id = {goal.subject_id: goal for goal in goals}

	subject_summaries = []
	for subject in Subject.objects.filter(user=request.user).prefetch_related('grades').order_by('name'):
		subject_grades = list(subject.grades.all())
		latest_grade = subject_grades[0] if subject_grades else None

		# Use CHED weighted average
		subject_average = _calculate_ched_weighted_average(subject)

		goal = goals_by_subject_id.get(subject.id)
		target_progress = None
		gap = None
		predicted_grade = None

		if goal and latest_grade is not None:
			gap = round(float(latest_grade.grade) - float(goal.target_grade), 2)
			if float(goal.target_grade) > 0:
				target_progress = min(round((float(latest_grade.grade) / float(goal.target_grade)) * 100, 1), 100)
			# Get predictive grade needed
			predicted_grade = _calculate_predictive_grade(subject, goal)

		subject_summaries.append(
			{
				'subject': subject,
				'latest_grade': latest_grade,
				'average': subject_average,
				'goal': goal,
				'gap': gap,
				'target_progress': target_progress,
				'predicted_grade': predicted_grade,
				'prediction_needed': predicted_grade is not None,
			}
		)

	notifications = request.user.notifications.all()[:5]
	unread_count = request.user.notifications.filter(is_read=False).count()

	context = {
		'overall_average': round(float(overall_average), 2) if overall_average is not None else None,
		'standing': _academic_standing(float(overall_average)) if overall_average is not None else 'No grades yet',
		'chart_labels_json': json.dumps(chart_labels),
		'chart_data_json': json.dumps(chart_data),
		'subject_summaries': subject_summaries,
		'notifications': notifications,
		'unread_count': unread_count,
		'recent_grades': grades.select_related('subject')[:10],
		'total_goals': goals.count(),
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

			# Get active goal and create notifications
			active_goal = Goal.objects.filter(user=request.user, subject=subject, active=True).order_by('-created_at').first()
			_create_enhanced_grade_notifications(request.user, subject, grade_entry.grade, active_goal)

			messages.success(request, f'Grade for {subject.name} was saved successfully.')
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


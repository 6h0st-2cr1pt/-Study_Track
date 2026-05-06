import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
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


def _create_grade_notifications(user, subject, grade_value):
	active_goal = Goal.objects.filter(user=user, subject=subject, active=True).order_by('-created_at').first()
	if active_goal and grade_value < active_goal.target_grade:
		Notification.objects.create(
			user=user,
			message=(
				f'Your {subject.name} grade of {grade_value} is below your target '
				f'of {active_goal.target_grade}.'
			),
		)
	if grade_value < 75:
		Notification.objects.create(
			user=user,
			message=f'Your {subject.name} grade of {grade_value} needs attention. Consider extra review time.',
		)


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
			StudentProfile.objects.get_or_create(user=user)
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

	chart_labels = [label for _, label in GradeEntry.PERIOD_CHOICES]
	period_map = {choice: 0.0 for choice, _ in GradeEntry.PERIOD_CHOICES}
	for row in period_average_rows:
		period_map[row['grading_period']] = round(float(row['avg']), 2)
	chart_data = [period_map[choice] for choice, _ in GradeEntry.PERIOD_CHOICES]

	goals = Goal.objects.filter(user=request.user, active=True).select_related('subject')
	goals_by_subject_id = {goal.subject_id: goal for goal in goals}

	subject_summaries = []
	for subject in Subject.objects.filter(user=request.user).prefetch_related('grades').order_by('name'):
		subject_grades = list(subject.grades.all())
		latest_grade = subject_grades[0] if subject_grades else None
		subject_average = None
		if subject_grades:
			subject_average = round(sum(float(grade.grade) for grade in subject_grades) / len(subject_grades), 2)
		goal = goals_by_subject_id.get(subject.id)
		target_progress = None
		gap = None
		if goal and latest_grade is not None:
			gap = round(float(latest_grade.grade) - float(goal.target_grade), 2)
			if float(goal.target_grade) > 0:
				target_progress = min(round((float(latest_grade.grade) / float(goal.target_grade)) * 100, 1), 100)
		subject_summaries.append(
			{
				'subject': subject,
				'latest_grade': latest_grade,
				'average': subject_average,
				'goal': goal,
				'gap': gap,
				'target_progress': target_progress,
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
			_create_grade_notifications(request.user, subject, grade_entry.grade)
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

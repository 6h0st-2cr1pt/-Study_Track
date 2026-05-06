from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class StudentProfile(models.Model):
	SEMESTER = 'semester'
	TRIMESTER = 'trimester'

	GRADING_STRUCTURE_CHOICES = [
		(SEMESTER, 'Semester (2 terms per year)'),
		(TRIMESTER, 'Trimester (3 terms per year)'),
	]

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
	institution = models.CharField(max_length=150, blank=True)
	program = models.CharField(max_length=150, blank=True)
	year_level = models.CharField(max_length=50, blank=True)
	grading_structure = models.CharField(
		max_length=20,
		choices=GRADING_STRUCTURE_CHOICES,
		default=SEMESTER,
		help_text='Select your school\'s academic calendar structure'
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f'{self.user.username} profile'


class Subject(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subjects')
	name = models.CharField(max_length=120)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['name']
		constraints = [
			models.UniqueConstraint(fields=['user', 'name'], name='unique_subject_per_student')
		]

	def __str__(self):
		return self.name


class GradeEntry(models.Model):
	PRELIM = 'prelim'
	MIDTERM = 'midterm'
	FINALS = 'final'
	PROJECT = 'project'

	PERIOD_CHOICES = [
		(PRELIM, 'Prelim'),
		(MIDTERM, 'Midterm'),
		(FINALS, 'Finals'),
		(PROJECT, 'Project'),
	]

	# CHED grading components
	ATTENDANCE = 'attendance'
	PARTICIPATION = 'participation'
	QUIZ = 'quiz'
	ASSIGNMENT = 'assignment'
	MIDTERM_EXAM = 'midterm_exam'
	FINAL_EXAM = 'final_exam'
	PROJECT_WORK = 'project_work'

	COMPONENT_CHOICES = [
		(ATTENDANCE, 'Attendance (10%)'),
		(PARTICIPATION, 'Participation (10%)'),
		(QUIZ, 'Quizzes (20%)'),
		(ASSIGNMENT, 'Assignments (20%)'),
		(MIDTERM_EXAM, 'Midterm Exam (20%)'),
		(FINAL_EXAM, 'Final Exam (20%)'),
		(PROJECT_WORK, 'Project Work (Custom %)'),
	]

	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grade_entries')
	subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')
	grading_period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
	grade = models.DecimalField(
		max_digits=5,
		decimal_places=2,
		validators=[MinValueValidator(0), MaxValueValidator(100)],
	)
	component = models.CharField(max_length=20, choices=COMPONENT_CHOICES, default=QUIZ, help_text='CHED grading component')
	component_weight = models.DecimalField(
		max_digits=5,
		decimal_places=2,
		default=1.0,
		validators=[MinValueValidator(0), MaxValueValidator(100)],
		help_text='Weight of this component (e.g., 20 means 20%)'
	)
	notes = models.TextField(blank=True)
	recorded_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-recorded_at']

	def __str__(self):
		return f'{self.subject.name} - {self.get_grading_period_display()}: {self.grade}'


class Goal(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
	subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='goals')
	target_grade = models.DecimalField(
		max_digits=5,
		decimal_places=2,
		validators=[MinValueValidator(0), MaxValueValidator(100)],
	)
	active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		state = 'Active' if self.active else 'Inactive'
		return f'{self.subject.name} goal ({self.target_grade}) - {state}'


class Notification(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
	message = models.TextField()
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.message[:50]

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class StudentProfile(models.Model):
	TWO_PERIODS = 'two_periods'
	THREE_PERIODS = 'three_periods'

	GRADING_PERIOD_CHOICES = [
		(TWO_PERIODS, 'Midterm, Endterm'),
		(THREE_PERIODS, 'Prelim, Midterm, Endterm'),
	]

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
	institution = models.CharField(max_length=150, blank=True)
	program = models.CharField(max_length=150, blank=True)
	year_level = models.CharField(max_length=50, blank=True)

	# Allow per-semester grading internal structure
	sem1_grading_periods = models.CharField(
		max_length=20,
		choices=GRADING_PERIOD_CHOICES,
		default=TWO_PERIODS,
		help_text='Grading periods for 1st Semester'
	)

	sem2_grading_periods = models.CharField(
		max_length=20,
		choices=GRADING_PERIOD_CHOICES,
		default=TWO_PERIODS,
		help_text='Grading periods for 2nd Semester'
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f'{self.user.username} profile'


class Subject(models.Model):
	YEAR_1 = '1'
	YEAR_2 = '2'
	YEAR_3 = '3'
	YEAR_4 = '4'
	YEAR_CHOICES = [
		(YEAR_1, '1st Year'),
		(YEAR_2, '2nd Year'),
		(YEAR_3, '3rd Year'),
		(YEAR_4, '4th Year'),
	]
	
	SEM_1 = '1'
	SEM_2 = '2'
	SEMESTER_CHOICES = [
		(SEM_1, '1st Semester'),
		(SEM_2, '2nd Semester'),
	]

	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subjects')
	name = models.CharField(max_length=120)
	year = models.CharField(max_length=1, choices=YEAR_CHOICES, default=YEAR_1)
	semester = models.CharField(max_length=1, choices=SEMESTER_CHOICES, default=SEM_1)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['year', 'semester', 'name']
		constraints = [
			models.UniqueConstraint(fields=['user', 'name', 'year', 'semester'], name='unique_subject_per_student_term')
		]

	def __str__(self):
		return f'{self.name} (Yr {self.year}, Sem {self.semester})'


class GradeEntry(models.Model):
	PRELIM = 'prelim'
	MIDTERM = 'midterm'
	ENDTERM = 'endterm'
	PROJECT = 'project'

	# All possible periods
	PERIOD_CHOICES = [
		(PRELIM, 'Prelim'),
		(MIDTERM, 'Midterm'),
		(ENDTERM, 'Endterm'),
		(PROJECT, 'Project'),
	]

	# Trimester periods: Prelim, Midterm, Endterm
	TRIMESTER_PERIOD_CHOICES = [
		(PRELIM, 'Prelim'),
		(MIDTERM, 'Midterm'),
		(ENDTERM, 'Endterm'),
	]

	# Semester periods: Midterm, Endterm
	SEMESTER_PERIOD_CHOICES = [
		(MIDTERM, 'Midterm'),
		(ENDTERM, 'Endterm'),
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
	component = models.CharField(max_length=20, choices=COMPONENT_CHOICES, default=QUIZ, blank=True, null=True, help_text='CHED grading component (optional)')
	component_weight = models.DecimalField(
		max_digits=5,
		decimal_places=2,
		default=1.0,
		blank=True,
		null=True,
		validators=[MinValueValidator(0), MaxValueValidator(100)],
		help_text='Weight of this component (optional)'
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
	# Semester for which this goal applies (useful for universities with multiple semesters)
	FIRST_SEM = '1'
	SECOND_SEM = '2'
	SEMESTER_CHOICES = [
		(FIRST_SEM, '1st Semester'),
		(SECOND_SEM, '2nd Semester'),
	]
	semester = models.CharField(max_length=2, choices=SEMESTER_CHOICES, default=FIRST_SEM)
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

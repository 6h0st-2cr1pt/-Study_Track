import json
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .data.bsis_curriculum import BSIS_CURRICULUM, iter_curriculum_subjects
from .models import GradeEntry, Goal, Notification, StudentProfile, Subject


class StudyTrackFlowTests(TestCase):
	def test_registration_creates_user_and_profile(self):
		response = self.client.post(
			reverse('register'),
			{
				'username': 'student1',
				'first_name': 'Student',
				'last_name': 'One',
				'email': 'student1@example.com',
				'grading_structure': 'semester',
				'password1': 'StrongPass123!!',
				'password2': 'StrongPass123!!',
			},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(User.objects.filter(username='student1').exists())
		self.assertTrue(StudentProfile.objects.filter(user__username='student1').exists())
		self.assertContains(response, 'StudyTrack')

	def test_grade_goal_and_notifications_flow(self):
		user = User.objects.create_user(username='student2', password='StrongPass123!')
		self.client.login(username='student2', password='StrongPass123!')
		subject = Subject.objects.create(user=user, name='Mathematics')

		goal_response = self.client.post(
			reverse('add_goal'),
			{
				'subject_name': 'Mathematics',
				'target_grade': '90',
				'active': 'on',
			},
			follow=True,
		)
		self.assertEqual(goal_response.status_code, 200)
		self.assertTrue(Subject.objects.filter(user=user, name='Mathematics').exists())

		grade_response = self.client.post(
			reverse('add_grade'),
			{
				'subject': str(subject.pk),
				'grading_period': 'midterm',
				'component': 'quiz',
				'grade': '88',
				'component_weight': '1.0',
				'notes': 'Solid work',
			},
			follow=True,
		)
		self.assertEqual(grade_response.status_code, 200)
		self.assertContains(grade_response, 'Grade for Mathematics was saved')
		self.assertContains(grade_response, '88')

		notifications = Notification.objects.filter(user=user)
		self.assertTrue(notifications.count() >= 1)
		self.assertTrue(any('below your target' in n.message for n in notifications))

		notifications_response = self.client.post(reverse('notifications'), follow=True)
		self.assertEqual(notifications_response.status_code, 200)
		self.assertTrue(Notification.objects.filter(user=user, is_read=False).count() == 0)

		goal_page = self.client.get(reverse('add_goal'))
		self.assertContains(goal_page, 'Add subject and goal')

	def test_dashboard_requires_login(self):
		response = self.client.get(reverse('dashboard'))
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('login'), response['Location'])

	def test_logout_redirects_to_login(self):
		User.objects.create_user(username='student3', password='StrongPass123!')
		self.client.login(username='student3', password='StrongPass123!')

		response = self.client.post(reverse('logout'), follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Login')
		self.assertFalse('_auth_user_id' in self.client.session)

	def test_auth_pages_do_not_render_sidebar(self):
		login_response = self.client.get(reverse('login'))
		register_response = self.client.get(reverse('register'))

		self.assertEqual(login_response.status_code, 200)
		self.assertEqual(register_response.status_code, 200)
		self.assertNotContains(login_response, '<aside class="sidebar"')
		self.assertNotContains(register_response, '<aside class="sidebar"')

	def test_goal_page_allows_subject_and_goal_entry(self):
		user = User.objects.create_user(username='student4', password='StrongPass123!')
		self.client.login(username='student4', password='StrongPass123!')

		response = self.client.get(reverse('add_goal'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Add subject and goal')
		self.assertContains(response, 'Create your subject and target grade first')
		self.assertNotContains(response, 'No subjects are available yet')

	def test_manage_profile_updates_user_and_student_profile(self):
		user = User.objects.create_user(username='student5', password='StrongPass123!', email='old@example.com')
		self.client.login(username='student5', password='StrongPass123!')

		response = self.client.post(
			reverse('manage_profile'),
			{
				'first_name': 'New',
				'last_name': 'Name',
				'email': 'new@example.com',
				'institution': 'State College',
				'program': 'BSIT',
				'year_level': '3rd Year',
				'grading_structure': 'semester',
			},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		user.refresh_from_db()
		profile = StudentProfile.objects.get(user=user)
		self.assertEqual(user.first_name, 'New')
		self.assertEqual(user.last_name, 'Name')
		self.assertEqual(user.email, 'new@example.com')
		self.assertEqual(profile.institution, 'State College')
		self.assertEqual(profile.program, 'BSIT')
		self.assertEqual(profile.year_level, '3rd Year')

	def test_sidebar_shows_manage_profile_link_and_icon(self):
		user = User.objects.create_user(username='student6', password='StrongPass123!')
		self.client.login(username='student6', password='StrongPass123!')

		response = self.client.get(reverse('dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Manage Profile')
		self.assertContains(response, 'cdn-icons-png.flaticon.com')

	def test_seed_bsis_curriculum_command_populates_fedorov(self):
		user = User.objects.create_user(username='Fedorov', password='StrongPass123!')
		buffer = StringIO()
		call_command('seed_bsis_curriculum', username='Fedorov', stdout=buffer)

		self.assertTrue(User.objects.filter(username='Fedorov').exists())
		expected_subjects = list(iter_curriculum_subjects())
		curriculum_subjects = Subject.objects.filter(user=user, name__in=[item['name'] for item in expected_subjects])
		self.assertEqual(curriculum_subjects.count(), len(expected_subjects))
		self.assertEqual(GradeEntry.objects.filter(user=user, subject__in=curriculum_subjects).count(), len(expected_subjects) * 2)
		self.assertEqual(Goal.objects.filter(user=user, subject__in=curriculum_subjects, active=True).count(), len(expected_subjects))

		for term in BSIS_CURRICULUM:
			self.assertEqual(
				Subject.objects.filter(
					user=user,
					year=term['year'],
					semester=term['semester'],
				).count(),
				len(term['subjects']),
			)

		for subject in curriculum_subjects:
			self.assertEqual(subject.grades.count(), 2)
			self.assertTrue(subject.grades.filter(grading_period=GradeEntry.MIDTERM).exists())
			self.assertTrue(subject.grades.filter(grading_period=GradeEntry.ENDTERM).exists())

		self.client.login(username='Fedorov', password='StrongPass123!')
		response = self.client.get(reverse('dashboard'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'gradesChart')
		self.assertContains(response, 'goalDistanceChart')

		context = response.context[-1]
		progress_tracking = json.loads(context['progress_tracking_json'])
		goal_distance = json.loads(context['goal_distance_json'])
		self.assertGreater(len(progress_tracking['1']['1']['subject_names']), 0)
		self.assertGreater(len(progress_tracking['1']['1']['datasets']), 0)
		self.assertGreater(len(goal_distance['1']['1']['subject_names']), 0)
		self.assertGreater(len(goal_distance['1']['1']['datasets']), 0)

		# Running the seed command again should not duplicate subjects, grades, or goals.
		call_command('seed_bsis_curriculum', username='Fedorov', stdout=StringIO())
		self.assertEqual(Subject.objects.filter(user=user, name__in=[item['name'] for item in expected_subjects]).count(), len(expected_subjects))
		self.assertEqual(GradeEntry.objects.filter(user=user, subject__in=curriculum_subjects).count(), len(expected_subjects) * 2)
		self.assertEqual(Goal.objects.filter(user=user, subject__in=curriculum_subjects, active=True).count(), len(expected_subjects))
		self.assertIn('BSIS curriculum seeded for user "Fedorov"', buffer.getvalue())


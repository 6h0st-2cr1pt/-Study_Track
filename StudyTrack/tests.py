from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Notification, StudentProfile, Subject


class StudyTrackFlowTests(TestCase):
	def test_registration_creates_user_and_profile(self):
		response = self.client.post(
			reverse('register'),
			{
				'username': 'student1',
				'first_name': 'Student',
				'last_name': 'One',
				'email': 'student1@example.com',
				'password1': 'StrongPass123!',
				'password2': 'StrongPass123!',
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
				'subject': str(subject.pk),
				'target_grade': '90',
				'active': 'on',
			},
			follow=True,
		)
		self.assertEqual(goal_response.status_code, 200)

		grade_response = self.client.post(
			reverse('add_grade'),
			{
				'subject_name': 'Mathematics',
				'grading_period': 'midterm',
				'grade': '88',
				'notes': 'Solid work',
			},
			follow=True,
		)
		self.assertEqual(grade_response.status_code, 200)
		self.assertContains(grade_response, 'Very Good')
		self.assertContains(grade_response, '88')

		notifications = Notification.objects.filter(user=user)
		self.assertEqual(notifications.count(), 1)
		self.assertIn('below your target', notifications.first().message)

		notifications_response = self.client.post(reverse('notifications'), follow=True)
		self.assertEqual(notifications_response.status_code, 200)
		self.assertTrue(Notification.objects.filter(user=user, is_read=False).count() == 0)

		goal_page = self.client.get(reverse('add_goal'))
		self.assertContains(goal_page, 'Mathematics')

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

	def test_goal_page_shows_empty_state_when_no_subjects(self):
		user = User.objects.create_user(username='student4', password='StrongPass123!')
		self.client.login(username='student4', password='StrongPass123!')

		response = self.client.get(reverse('add_goal'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'No subjects are available yet')

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


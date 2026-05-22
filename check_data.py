#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_track.settings')
django.setup()

from django.contrib.auth.models import User
from StudyTrack.models import Subject, Goal, GradeEntry, StudentProfile

user = User.objects.first()
if user:
    print(f'User: {user.username}')
    print(f'\nSubjects:')
    subjects = Subject.objects.filter(user=user)
    for subj in subjects:
        print(f'  - {subj.name}')

    print(f'\nGoals (Semester 1):')
    for goal in Goal.objects.filter(user=user, semester=Goal.FIRST_SEM, active=True):
        print(f'  - {goal.subject.name}: target {goal.target_grade}')

    print(f'\nGoals (Semester 2):')
    for goal in Goal.objects.filter(user=user, semester=Goal.SECOND_SEM, active=True):
        print(f'  - {goal.subject.name}: target {goal.target_grade}')

    print(f'\nGrades (first 15):')
    for grade in GradeEntry.objects.filter(user=user).order_by('-recorded_at')[:15]:
        print(f'  - {grade.subject.name} ({grade.get_grading_period_display()}): {grade.grade}')

    profile = StudentProfile.objects.get_or_create(user=user)[0]
    print(f'\nProfile:')
    print(f'  - Semester 1 structure: {profile.get_sem1_structure_display()}')
    print(f'  - Semester 2 structure: {profile.get_sem2_structure_display()}')
else:
    print('No users found')


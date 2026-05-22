#!/usr/bin/env python
"""
Test script to verify semester separation works correctly.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_track.settings')
django.setup()

from django.contrib.auth.models import User
from StudyTrack.models import Subject, Goal

print("=" * 60)
print("SEMESTER SEPARATION TEST")
print("=" * 60)

user = User.objects.first()
if not user:
    print("No users found!")
    sys.exit(1)

print(f"\nUser: {user.username}\n")

# Get all subjects
subjects = Subject.objects.filter(user=user)
print(f"Total subjects: {subjects.count()}\n")

# Check 1st semester goals
sem1_goals = Goal.objects.filter(user=user, semester=Goal.FIRST_SEM, active=True)
print("1st Semester Goals:")
for goal in sem1_goals:
    print(f"  ✓ {goal.subject.name}: target {goal.target_grade}")
print(f"Total: {sem1_goals.count()}\n")

# Check 2nd semester goals
sem2_goals = Goal.objects.filter(user=user, semester=Goal.SECOND_SEM, active=True)
print("2nd Semester Goals:")
for goal in sem2_goals:
    print(f"  ✓ {goal.subject.name}: target {goal.target_grade}")
print(f"Total: {sem2_goals.count()}\n")

# Test the separator: subjects should only appear in their assigned semester
print("Separation Test:")
print("-" * 60)

sem1_subjects = set(g.subject_id for g in sem1_goals)
sem2_subjects = set(g.subject_id for g in sem2_goals)
overlap = sem1_subjects & sem2_subjects

if overlap:
    print("⚠ WARNING: The following subjects appear in BOTH 1st and 2nd semester:")
    for subj_id in overlap:
        subj_name = Subject.objects.get(id=subj_id).name
        print(f"  - {subj_name}")
else:
    print("✓ PASS: No subjects appear in both semesters")

print()

# Test the expectation: if a semester has NO goals, it should have NO entries
if sem2_goals.count() == 0:
    print("✓ PASS: 2nd semester table will be empty (no sem2 goals)")
else:
    print("✓ INFO: 2nd semester table will have entries")

print("\n" + "=" * 60)
print("Test completed.")
print("=" * 60)


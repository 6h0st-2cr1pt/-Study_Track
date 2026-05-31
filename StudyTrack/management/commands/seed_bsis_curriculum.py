import hashlib
import random

from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from StudyTrack.data.bsis_curriculum import BSIS_CURRICULUM, iter_curriculum_subjects
from StudyTrack.models import GradeEntry, Goal, Subject


YEAR_GRADE_PROFILES = {
    '1': {
        GradeEntry.MIDTERM: (85.2, 3.2),
        GradeEntry.ENDTERM: (86.8, 3.0),
        'goal': (89.0, 94.0),
    },
    '2': {
        GradeEntry.MIDTERM: (83.8, 3.5),
        GradeEntry.ENDTERM: (85.2, 3.3),
        'goal': (87.0, 92.0),
    },
    '3': {
        GradeEntry.MIDTERM: (82.0, 3.8),
        GradeEntry.ENDTERM: (83.6, 3.6),
        'goal': (85.0, 90.0),
    },
    '4': {
        GradeEntry.MIDTERM: (80.8, 4.1),
        GradeEntry.ENDTERM: (82.4, 3.8),
        'goal': (83.0, 88.0),
    },
}


def _seeded_rng(*parts):
    seed_value = '|'.join(str(part) for part in parts)
    seed_bytes = hashlib.sha256(seed_value.encode('utf-8')).digest()
    return random.Random(int.from_bytes(seed_bytes[:8], 'big'))


def _subject_adjustment(subject_name):
    name = subject_name.upper()
    if 'PHYSICAL EDUCATION' in name or 'NSTP' in name:
        return {'grade_bonus': 2.8, 'goal_bonus': 2.0}
    if 'ELECTIVE' in name:
        return {'grade_bonus': 1.2, 'goal_bonus': 1.0}
    if 'CAPSTONE' in name or 'PRACTICUM' in name:
        return {'grade_bonus': 0.9, 'goal_bonus': 0.0}
    if 'RESEARCH' in name:
        return {'grade_bonus': 0.0, 'goal_bonus': 0.0}
    if 'PROGRAMMING' in name or 'DATABASE' in name or 'NETWORK' in name or 'SYSTEMS' in name:
        return {'grade_bonus': -0.4, 'goal_bonus': -0.5}
    return {'grade_bonus': 0.4, 'goal_bonus': 0.0}


def _stable_random_grade(username, subject_name, year, semester, period):
    profile = YEAR_GRADE_PROFILES[year]
    mean, stdev = profile[period]
    adj = _subject_adjustment(subject_name)
    rng = _seeded_rng(username, subject_name, year, semester, period, 'grade')
    value = rng.gauss(mean + adj['grade_bonus'], stdev)
    return Decimal(f'{max(75.0, min(98.0, value)):.2f}')


def _stable_random_goal(username, subject_name, year, semester):
    low, high = YEAR_GRADE_PROFILES[year]['goal']
    adj = _subject_adjustment(subject_name)
    rng = _seeded_rng(username, subject_name, year, semester, 'goal')
    value = rng.uniform(low, high) + adj['goal_bonus']
    return Decimal(f'{max(80.0, min(97.0, value)):.2f}')


class Command(BaseCommand):
    help = 'Seed a BSIS curriculum and random sample grades for a user (defaults to Fedorov).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            default='Fedorov',
            help='Username to seed the BSIS subject curriculum for.',
        )
        parser.add_argument(
            '--create-user',
            action='store_true',
            help='Create the user if it does not already exist.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options['username']
        create_user = options['create_user']
        curriculum_items = list(iter_curriculum_subjects())

        user = User.objects.filter(username=username).first()
        created_user = False
        if user is None:
            if not create_user:
                user = User.objects.create(username=username)
                user.set_unusable_password()
                user.save(update_fields=['password'])
                created_user = True
            else:
                user = User.objects.create_user(username=username)
                user.set_unusable_password()
                user.save(update_fields=['password'])
                created_user = True

        created_subjects = 0
        updated_subjects = 0
        created_grades = 0
        updated_grades = 0
        removed_duplicate_grades = 0
        created_goals = 0
        updated_goals = 0
        removed_duplicate_goals = 0

        for item in curriculum_items:
            subject, created = Subject.objects.get_or_create(
                user=user,
                name=item['name'],
                year=item['year'],
                semester=item['semester'],
            )
            if created:
                created_subjects += 1
            else:
                updated_subjects += 1

            for period in (GradeEntry.MIDTERM, GradeEntry.ENDTERM):
                grade_value = _stable_random_grade(user.username, subject.name, subject.year, subject.semester, period)
                existing_grades = list(
                    GradeEntry.objects.filter(user=user, subject=subject, grading_period=period).order_by('recorded_at')
                )
                notes = 'Auto-generated BSIS sample grade.'

                if not existing_grades:
                    GradeEntry.objects.create(
                        user=user,
                        subject=subject,
                        grading_period=period,
                        grade=grade_value,
                        notes=notes,
                    )
                    created_grades += 1
                else:
                    grade_entry = existing_grades[-1]
                    grade_entry.grade = grade_value
                    grade_entry.notes = notes
                    grade_entry.save(update_fields=['grade', 'notes'])
                    updated_grades += 1

                    for duplicate in existing_grades[:-1]:
                        duplicate.delete()
                        removed_duplicate_grades += 1

            goal_target = _stable_random_goal(user.username, subject.name, subject.year, subject.semester)
            existing_goals = list(
                Goal.objects.filter(user=user, subject=subject).order_by('created_at')
            )
            if not existing_goals:
                Goal.objects.create(
                    user=user,
                    subject=subject,
                    target_grade=goal_target,
                    active=True,
                    semester=subject.semester,
                )
                created_goals += 1
            else:
                goal = existing_goals[-1]
                goal.target_grade = goal_target
                goal.active = True
                goal.semester = subject.semester
                goal.save(update_fields=['target_grade', 'active', 'semester'])
                updated_goals += 1

                for duplicate in existing_goals[:-1]:
                    duplicate.delete()
                    removed_duplicate_goals += 1

        total_subjects = Subject.objects.filter(user=user).count()
        total_grades = GradeEntry.objects.filter(user=user).count()
        curriculum_subjects = Subject.objects.filter(
            user=user,
            name__in=[item['name'] for item in curriculum_items],
        )
        curriculum_grades = GradeEntry.objects.filter(user=user, subject__in=curriculum_subjects).count()
        curriculum_goals = Goal.objects.filter(user=user, subject__in=curriculum_subjects, active=True).count()
        year_counts = {}
        for year_code, year_label in Subject.YEAR_CHOICES:
            year_counts[year_label] = Subject.objects.filter(user=user, year=year_code).count()

        self.stdout.write(self.style.SUCCESS(f'BSIS curriculum seeded for user "{user.username}".'))
        if created_user:
            self.stdout.write(self.style.WARNING('The user did not exist and was created with an unusable password.'))
        self.stdout.write(self.style.SUCCESS(f'Created {created_subjects} subjects; {updated_subjects} already existed.'))
        self.stdout.write(self.style.SUCCESS(f'Created {created_grades} grades; {updated_grades} already existed and were refreshed.'))
        self.stdout.write(self.style.SUCCESS(f'Removed {removed_duplicate_grades} duplicate grades.'))
        self.stdout.write(self.style.SUCCESS(f'Created {created_goals} goals; {updated_goals} already existed and were refreshed.'))
        self.stdout.write(self.style.SUCCESS(f'Removed {removed_duplicate_goals} duplicate goals.'))
        self.stdout.write(self.style.SUCCESS(f'BSIS curriculum subjects: {curriculum_subjects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'BSIS curriculum grades: {curriculum_grades}'))
        self.stdout.write(self.style.SUCCESS(f'BSIS curriculum goals: {curriculum_goals}'))
        self.stdout.write(self.style.SUCCESS(f'Total subjects for user: {total_subjects}'))
        self.stdout.write(self.style.SUCCESS(f'Total grades for user: {total_grades}'))
        self.stdout.write(self.style.SUCCESS(f'Year distribution: {year_counts}'))
        self.stdout.write(self.style.SUCCESS(f'Semesters covered: {len(BSIS_CURRICULUM)} terms across 1st to 4th year.'))


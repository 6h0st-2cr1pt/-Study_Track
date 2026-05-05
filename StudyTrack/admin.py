from django.contrib import admin

from .models import GradeEntry, Goal, Notification, StudentProfile, Subject


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'institution', 'program', 'year_level', 'updated_at')
	search_fields = ('user__username', 'user__email', 'institution', 'program')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
	list_display = ('name', 'user', 'created_at')
	search_fields = ('name', 'user__username')
	list_filter = ('created_at',)


@admin.register(GradeEntry)
class GradeEntryAdmin(admin.ModelAdmin):
	list_display = ('subject', 'user', 'grading_period', 'grade', 'recorded_at')
	list_filter = ('grading_period', 'recorded_at')
	search_fields = ('subject__name', 'user__username')


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
	list_display = ('subject', 'user', 'target_grade', 'active', 'created_at')
	list_filter = ('active', 'created_at')
	search_fields = ('subject__name', 'user__username')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ('user', 'is_read', 'created_at')
	list_filter = ('is_read', 'created_at')
	search_fields = ('user__username', 'message')

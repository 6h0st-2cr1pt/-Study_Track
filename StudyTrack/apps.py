from django.apps import AppConfig


class StudytrackConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'StudyTrack'

    def ready(self):
        from . import signals  # noqa: F401


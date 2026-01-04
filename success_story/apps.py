from django.apps import AppConfig


class SuccessstoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'success_story'

    def ready(self):
        from . import signals  # noqa: F401

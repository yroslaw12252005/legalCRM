from django.apps import AppConfig


class LeadsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'leads'

    def ready(self):
        import legalCRM.signals  # noqa: F401
        from .novofon import start_auto_monitor

        start_auto_monitor()

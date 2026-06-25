from django.apps import AppConfig


class CallRecordingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "call_recording"

    def ready(self):
        from .services import start_auto_monitor

        start_auto_monitor()


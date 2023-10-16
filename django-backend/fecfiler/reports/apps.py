from django.apps import AppConfig


class ReportsConfig(AppConfig):
    name = "fecfiler.reports"

    def ready(self):
        # Implicitly connect a signal handlers decorated with @receiver.
        from . import signals  # noqa

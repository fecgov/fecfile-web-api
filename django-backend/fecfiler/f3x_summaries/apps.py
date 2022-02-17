from django.apps import AppConfig


class F3XSummariesConfig(AppConfig):
    name = 'fecfiler.f3x_summaries'

    def ready(self):
        # Implicitly connect a signal handlers decorated with @receiver.
        from . import signals # noqa

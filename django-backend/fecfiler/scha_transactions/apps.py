from django.apps import AppConfig


class SchedAConfig(AppConfig):
    name = 'fecfiler.scha_transactions'

    def ready(self):
        # Implicitly connect a signal handlers decorated with @receiver.
        from . import signals

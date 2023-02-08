from django.apps import AppConfig


class MockOpenFecConfig(AppConfig):
    name = 'fecfiler.mock_openfec'

    def ready(self):
        # Implicitly connect a signal handlers decorated with @receiver.
        from . import signals # noqa

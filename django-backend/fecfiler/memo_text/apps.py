from django.apps import AppConfig


class MemoTextConfig(AppConfig):
    name = 'fecfiler.memo_text'

    def ready(self):
        # Implicitly connect a signal handlers decorated with @receiver.
        from . import signals # noqa

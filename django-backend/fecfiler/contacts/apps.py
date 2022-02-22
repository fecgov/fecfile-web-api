from django.apps import AppConfig


class ContactsConfig(AppConfig):
    name = 'fecfiler.contacts'

    def ready(self):
        # Implicitly connect a signal handlers decorated with @receiver.
        from . import signals # noqa
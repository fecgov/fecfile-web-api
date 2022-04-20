from django.apps import AppConfig


class CommitteeAccountsConfig(AppConfig):
    name = 'fecfiler.committee_accounts'

    def ready(self):
        # Implicitly connect a signal handlers decorated with @receiver.
        from . import signals # noqa
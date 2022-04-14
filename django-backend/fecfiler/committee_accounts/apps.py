"""Django App Config for Committee Accounts"""
from django.apps import AppConfig


class CommitteeAccountsConfig(AppConfig):
    """Overrides of :py:func:`AppConfig.ready` to activate signals"""

    name = "fecfiler.committee_accounts"

    def ready(self):
        """Importing signals implicitly connects signal handlers decorated with
        @receiver."""
        from . import signals  # noqa

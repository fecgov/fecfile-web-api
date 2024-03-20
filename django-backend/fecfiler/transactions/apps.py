from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    name = "fecfiler.transactions"

    def ready(self):
        # Implicitly connect a signal handlers decorated with @receiver.
        from . import signals  # noqa

        from fecfiler.committee_accounts.models import CommitteeAccount
        from fecfiler.committee_accounts.views import create_committee_view

        for committee in CommitteeAccount.objects.all():
            create_committee_view(committee.id)

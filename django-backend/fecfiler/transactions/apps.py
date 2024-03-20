from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    name = "fecfiler.transactions"

    print("LOAING TRANSACTION APP")

    def ready(self):
        # Implicitly connect a signal handlers decorated with @receiver.
        from . import signals  # noqa

from fecfiler.transactions.schedule_a.models import ScheduleATransaction
from fecfiler.transactions.schedule_b.models import ScheduleBTransaction
from functools import reduce


def get_transaction_models():
    return [
        ScheduleATransaction._meta.model_name,
        ScheduleBTransaction._meta.model_name,
    ]


def get_related_transaction(instance):
    def get_transaction_from_table(found_transaction, model_name):
        if found_transaction:
            return found_transaction
        reverse_set = getattr(instance, f"{model_name}_set")
        return reverse_set.first()

    return reduce(get_transaction_from_table, get_transaction_models(), None)

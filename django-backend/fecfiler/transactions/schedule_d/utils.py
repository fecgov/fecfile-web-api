from fecfiler.transactions.models import Transaction
from django.forms.models import model_to_dict
from fecfiler.utils import save_copy
from django.db.models import Q
from decimal import Decimal


def add_schedule_d_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        data["creditor_organization_name"] = instance.contact_1.name
        data["creditor_last_name"] = instance.contact_1.last_name
        data["creditor_first_name"] = instance.contact_1.first_name
        data["creditor_middle_name"] = instance.contact_1.middle_name
        data["creditor_prefix"] = instance.contact_1.prefix
        data["creditor_suffix"] = instance.contact_1.suffix
        data["creditor_street_1"] = instance.contact_1.street_1
        data["creditor_street_2"] = instance.contact_1.street_2
        data["creditor_city"] = instance.contact_1.city
        data["creditor_state"] = instance.contact_1.state
        data["creditor_zip"] = instance.contact_1.zip

    if representation:
        representation.update(data)
    else:
        for k, v in data.items():
            setattr(instance, k, v)


def carry_forward_debts(report):
    if report.previous_report:
        debts_to_carry_forward = Transaction.objects.transaction_view().filter(
            ~Q(balance_at_close=Decimal(0)) | Q(balance_at_close__isnull=True),
            ~Q(memo_code=True),
            reports=report.previous_report,
            schedule_d_id__isnull=False,
            committee_account__id=report.committee_account.id,
        )

        for debt in debts_to_carry_forward:
            carry_forward_debt(debt, report)


def carry_forward_debt(debt, report):
    debt_data = {
        "schedule_d": save_copy(
            debt.schedule_d,
            {
                "incurred_amount": Decimal(0),
                "report_coverage_from_date": report.coverage_from_date,
            },
        ),
        "contact_1_id": debt.contact_1_id,
        "contact_2_id": debt.contact_2_id,
        "contact_3_id": debt.contact_3_id,
        "committee_account_id": debt.committee_account_id,
        # The debt_id should point to the original debt transaction
        # even if the debt is pulled forward multiple times.
        "debt_id": debt.debt_id or debt.id,
    }
    return save_copy(
        Transaction(
            **model_to_dict(
                debt,
                fields=[f.name for f in Transaction._meta.fields],
                exclude=[
                    "committee_account",
                    "report",
                    "contact_1",
                    "contact_2",
                    "contact_3",
                    "schedule_d",
                    "debt",
                ],
            )
        ),
        debt_data,
        links={"reports": [report]},
    )

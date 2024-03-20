from fecfiler.transactions.models import Transaction
from django.forms.models import model_to_dict
from fecfiler.utils import save_copy


def add_schedule_c2_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        data["guarantor_last_name"] = instance.contact_1.last_name
        data["guarantor_first_name"] = instance.contact_1.first_name
        data["guarantor_middle_name"] = instance.contact_1.middle_name
        data["guarantor_prefix"] = instance.contact_1.prefix
        data["guarantor_suffix"] = instance.contact_1.suffix
        data["guarantor_street_1"] = instance.contact_1.street_1
        data["guarantor_street_2"] = instance.contact_1.street_2
        data["guarantor_city"] = instance.contact_1.city
        data["guarantor_state"] = instance.contact_1.state
        data["guarantor_zip"] = instance.contact_1.zip
        data["guarantor_employer"] = instance.contact_1.employer
        data["guarantor_occupation"] = instance.contact_1.occupation

    if representation:
        representation.update(data)
    else:
        for k, v in data.items():
            setattr(instance, k, v)


def carry_forward_guarantor(report, new_loan, guarantor):
    print("AHOY CARRY FORWARD GUARANTOR")
    save_copy(
        Transaction(
            **model_to_dict(
                guarantor,
                fields=[f.name for f in Transaction._meta.fields],
                exclude=[
                    "committee_account",
                    "report",
                    "parent_transaction",
                    "contact_1",
                    "contact_2",
                    "contact_3",
                    "schedule_c2",
                ],
            )
        ),
        {
            "contact_1_id": guarantor.contact_1_id,
            "contact_2_id": guarantor.contact_2_id,
            "contact_2_id": guarantor.contact_2_id,
            "schedule_c2": save_copy(guarantor.schedule_c2),
            "memo_text": (
                save_copy(guarantor.memo_text) if guarantor.memo_text else None
            ),
            "committee_account_id": new_loan.committee_account_id,
            "report_id": report.id,
            "parent_transaction_id": new_loan.id,
        },
    )

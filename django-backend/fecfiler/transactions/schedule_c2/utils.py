from fecfiler.transactions.models import Transaction
from django.forms.models import model_to_dict
from fecfiler.utils import save_copy
from ..utils import add_org_ind_contact


def add_schedule_c2_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        add_org_ind_contact(data, instance.contact_1, "guarantor")
        data["guarantor_entity"] = instance.contact_1.type
        data["guarantor_committee_fec_id"] = instance.contact_1.committee_id
        data["guarantor_employer"] = instance.contact_1.employer
        data["guarantor_occupation"] = instance.contact_1.occupation

    if representation:
        representation.update(data)
    else:
        for k, v in data.items():
            setattr(instance, k, v)


def carry_forward_guarantor(report, new_loan, guarantor):
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
            "contact_3_id": guarantor.contact_3_id,
            "schedule_c2": save_copy(guarantor.schedule_c2),
            "committee_account_id": new_loan.committee_account_id,
            "report_id": report.id,
            "parent_transaction_id": new_loan.id,
        },
        links={"reports": [report]},
    )

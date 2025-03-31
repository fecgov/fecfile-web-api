from ..utils import add_org_ind_contact, add_candidate_contact, add_committee_contact
from fecfiler.transactions.models import Transaction


def add_schedule_f_contact_fields(instance: Transaction, representation=None):
    data = {}
    if instance.contact_1:
        add_org_ind_contact(data, instance.contact_1, "payee")
    if instance.contact_2:
        add_candidate_contact(data, instance.contact_2, "payee", False)
    if instance.contact_3:
        data["payee_committee_id_number"] = instance.contact_3.committee_id
    if instance.contact_4:
        data["designating_committee_id_number"] = instance.contact_4.committee_id
        data["designating_committee_name"] = instance.contact_4.name
    if instance.contact_5:
        add_committee_contact(data, instance.contact_5, "subordinate")

    if representation:
        representation.update(data)
    else:
        for k, v in data.items():
            setattr(instance, k, v)

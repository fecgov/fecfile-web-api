from ..utils import add_org_ind_contact, add_candidate_contact, add_committee_contact


def add_schedule_f_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        add_org_ind_contact(data, instance.contact_1, "payee")
    if instance.contact_2:
        add_candidate_contact(data, instance.contact_2, "payee", False)
    if instance.contact_3:
        add_committee_contact(data, instance.contact_3, "subordinate")

    if representation:
        representation.update(data)
    else:
        for k, v in data.items():
            setattr(instance, k, v)

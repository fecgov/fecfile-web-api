from ..utils import add_org_ind_contact, add_candidate_contact


def add_schedule_e_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        add_org_ind_contact(data, instance.contact_1, "payee")
    if instance.contact_2:
        add_candidate_contact(data, instance.contact_2, "so", False)

        # We do not update contact candidate state if presidential primary,
        # instead, we update/pull from the state from the transaction object
        data["so_candidate_state"] = (
            instance.schedule_e.so_candidate_state
            if instance.schedule_e
            and instance.schedule_e.election_code
            and instance.schedule_e.election_code.startswith("P")
            and instance.contact_2.candidate_office == "P"
            else instance.contact_2.candidate_state
        )

    if representation:
        representation.update(data)
    else:
        for k, v in data.items():
            setattr(instance, k, v)

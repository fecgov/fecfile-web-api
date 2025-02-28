from ..utils import add_location


def add_schedule_c1_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        add_location(data, instance.contact_1, "lender")
        data["lender_organization_name"] = instance.contact_1.name

    if representation:
        representation.update(data)
    else:
        for k, v in data.items():
            setattr(instance, k, v)

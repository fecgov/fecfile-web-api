def add_schedule_c1_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        data['lender_organization_name'] = instance.contact_1.name
        data['lender_street_1'] = instance.contact_1.street_1
        data['lender_street_2'] = instance.contact_1.street_2
        data['lender_city'] = instance.contact_1.city
        data['lender_state'] = instance.contact_1.state
        data['lender_zip'] = instance.contact_1.zip

    if representation:
        representation.update(data)
    else:
        for (k, v) in data.items():
            setattr(instance, k, v)

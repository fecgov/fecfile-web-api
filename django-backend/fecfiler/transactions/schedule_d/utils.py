def add_schedule_d_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        data['creditor_organization_name'] = instance.contact_1.name
        data['creditor_last_name'] = instance.contact_1.last_name
        data['creditor_first_name'] = instance.contact_1.first_name
        data['creditor_middle_name'] = instance.contact_1.middle_name
        data['creditor_prefix'] = instance.contact_1.prefix
        data['creditor_suffix'] = instance.contact_1.suffix
        data['creditor_street_1'] = instance.contact_1.street_1
        data['creditor_street_2'] = instance.contact_1.street_2
        data['creditor_city'] = instance.contact_1.city
        data['creditor_state'] = instance.contact_1.state
        data['creditor_zip'] = instance.contact_1.zip

    if representation:
        representation.update(data)
    else:
        for (k, v) in data.items():
            setattr(instance, k, v)

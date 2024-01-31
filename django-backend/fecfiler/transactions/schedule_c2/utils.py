def add_schedule_c2_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        data['guarantor_last_name'] = instance.contact_1.last_name
        data['guarantor_first_name'] = instance.contact_1.first_name
        data['guarantor_middle_name'] = instance.contact_1.middle_name
        data['guarantor_prefix'] = instance.contact_1.prefix
        data['guarantor_suffix'] = instance.contact_1.suffix
        data['guarantor_street_1'] = instance.contact_1.street_1
        data['guarantor_street_2'] = instance.contact_1.street_2
        data['guarantor_city'] = instance.contact_1.city
        data['guarantor_state'] = instance.contact_1.state
        data['guarantor_zip'] = instance.contact_1.zip
        data['guarantor_employer'] = instance.contact_1.employer
        data['guarantor_occupation'] = instance.contact_1.occupation

    if representation:
        representation.update(data)
    else:
        for (k, v) in data.items():
            setattr(instance, k, v)

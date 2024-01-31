def add_schedule_e_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        data['payee_organization_name'] = instance.contact_1.name
        data['payee_last_name'] = instance.contact_1.last_name
        data['payee_first_name'] = instance.contact_1.first_name
        data['payee_middle_name'] = instance.contact_1.middle_name
        data['payee_prefix'] = instance.contact_1.prefix
        data['payee_suffix'] = instance.contact_1.suffix
        data['payee_street_1'] = instance.contact_1.street_1
        data['payee_street_2'] = instance.contact_1.street_2
        data['payee_city'] = instance.contact_1.city
        data['payee_state'] = instance.contact_1.state
        data['payee_zip'] = instance.contact_1.zip
    if instance.contact_2:
        data['so_candidate_id_number'] = instance.contact_2.candidate_id
        data['so_candidate_last_name'] = instance.contact_2.last_name
        data['so_candidate_first_name'] = instance.contact_2.first_name
        data['so_candidate_middle_name'] = instance.contact_2.middle_name
        data['so_candidate_prefix'] = instance.contact_2.prefix
        data['so_candidate_suffix'] = instance.contact_2.suffix
        data['so_candidate_office'] = instance.contact_2.candidate_office
        data['so_candidate_district'] = instance.contact_2.candidate_district
        data['so_candidate_state'] = instance.contact_2.candidate_state

    if representation:
        representation.update(data)
    else:
        for (k, v) in data.items():
            setattr(instance, k, v)

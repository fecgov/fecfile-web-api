def add_schedule_c_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        data['lender_organization_name'] = instance.contact_1.name
        data['lender_last_name'] = instance.contact_1.last_name
        data['lender_first_name'] = instance.contact_1.first_name
        data['lender_middle_name'] = instance.contact_1.middle_name
        data['lender_prefix'] = instance.contact_1.prefix
        data['lender_suffix'] = instance.contact_1.suffix
        data['lender_street_1'] = instance.contact_1.street_1
        data['lender_street_2'] = instance.contact_1.street_2
        data['lender_city'] = instance.contact_1.city
        data['lender_state'] = instance.contact_1.state
        data['lender_zip'] = instance.contact_1.zip
        data['lender_committee_id_number'] = instance.contact_1.committee_id
    if instance.contact_2:
        data['lender_candidate_id_number'] = instance.contact_2.candidate_id
        data['lender_candidate_first_name'] = instance.contact_2.first_name
        data['lender_candidate_last_name'] = instance.contact_2.last_name
        data['lender_candidate_middle_name'] = instance.contact_2.middle_name
        data['lender_candidate_prefix'] = instance.contact_2.prefix
        data['lender_candidate_suffix'] = instance.contact_2.suffix
        data['lender_candidate_office'] = instance.contact_2.candidate_office
        data['lender_candidate_state'] = instance.contact_2.candidate_state
        data['lender_candidate_district'] = instance.contact_2.candidate_district

    if representation:
        representation.update(data)
    else:
        for (k, v) in data.items():
            setattr(instance, k, v)

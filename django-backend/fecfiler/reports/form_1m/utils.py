def add_form_1m_contact_fields(form_1m, representation):

    contact_key = 'contact_affiliated'
    if form_1m.get(contact_key):
        representation['affiliated_committee_fec_id'] = (
            form_1m[contact_key]['committee_id']
        )
        representation['affiliated_committee_name'] = form_1m[contact_key]['name']

    contact_key = 'contact_candidate_I'
    if form_1m.get(contact_key):
        representation['I_candidate_id_number'] = form_1m[contact_key]['candidate_id']
        representation['I_candidate_last_name'] = form_1m[contact_key]['last_name']
        representation['I_candidate_first_name'] = form_1m[contact_key]['first_name']
        representation['I_candidate_middle_name'] = form_1m[contact_key]['middle_name']
        representation['I_candidate_prefix'] = form_1m[contact_key]['prefix']
        representation['I_candidate_suffix'] = form_1m[contact_key]['suffix']
        representation['I_candidate_office'] = form_1m[contact_key]['candidate_office']
        representation['I_candidate_district'] = (
            form_1m[contact_key]['candidate_district']
        )
        representation['I_candidate_state'] = form_1m[contact_key]['candidate_state']

    contact_key = 'contact_candidate_II'
    if form_1m.get(contact_key):
        representation['II_candidate_id_number'] = form_1m[contact_key]['candidate_id']
        representation['II_candidate_last_name'] = form_1m[contact_key]['last_name']
        representation['II_candidate_first_name'] = form_1m[contact_key]['first_name']
        representation['II_candidate_middle_name'] = form_1m[contact_key]['middle_name']
        representation['II_candidate_prefix'] = form_1m[contact_key]['prefix']
        representation['II_candidate_suffix'] = form_1m[contact_key]['suffix']
        representation['II_candidate_office'] = form_1m[contact_key]['candidate_office']
        representation['II_candidate_district'] = (
            form_1m[contact_key]['candidate_district']
        )
        representation['II_candidate_state'] = form_1m[contact_key]['candidate_state']

    contact_key = 'contact_candidate_III'
    if form_1m.get(contact_key):
        representation['III_candidate_id_number'] = form_1m[contact_key]['candidate_id']
        representation['III_candidate_last_name'] = form_1m[contact_key]['last_name']
        representation['III_candidate_first_name'] = form_1m[contact_key]['first_name']
        representation['III_candidate_middle_name'] = form_1m[contact_key]['middle_name']
        representation['III_candidate_prefix'] = form_1m[contact_key]['prefix']
        representation['III_candidate_suffix'] = form_1m[contact_key]['suffix']
        representation['III_candidate_office'] = form_1m[contact_key]['candidate_office']
        representation['III_candidate_district'] = (
            form_1m[contact_key]['candidate_district']
        )
        representation['III_candidate_state'] = form_1m[contact_key]['candidate_state']

    contact_key = 'contact_candidate_IV'
    if form_1m.get(contact_key):
        representation['IV_candidate_id_number'] = form_1m[contact_key]['candidate_id']
        representation['IV_candidate_last_name'] = form_1m[contact_key]['last_name']
        representation['IV_candidate_first_name'] = form_1m[contact_key]['first_name']
        representation['IV_candidate_middle_name'] = form_1m[contact_key]['middle_name']
        representation['IV_candidate_prefix'] = form_1m[contact_key]['prefix']
        representation['IV_candidate_suffix'] = form_1m[contact_key]['suffix']
        representation['IV_candidate_office'] = form_1m[contact_key]['candidate_office']
        representation['IV_candidate_district'] = (
            form_1m[contact_key]['candidate_district']
        )
        representation['IV_candidate_state'] = form_1m[contact_key]['candidate_state']

    contact_key = 'contact_candidate_V'
    if form_1m.get(contact_key):
        representation['V_candidate_id_number'] = form_1m[contact_key]['candidate_id']
        representation['V_candidate_last_name'] = form_1m[contact_key]['last_name']
        representation['V_candidate_first_name'] = form_1m[contact_key]['first_name']
        representation['V_candidate_middle_name'] = form_1m[contact_key]['middle_name']
        representation['V_candidate_prefix'] = form_1m[contact_key]['prefix']
        representation['V_candidate_suffix'] = form_1m[contact_key]['suffix']
        representation['V_candidate_office'] = form_1m[contact_key]['candidate_office']
        representation['V_candidate_district'] = (
            form_1m[contact_key]['candidate_district']
        )
        representation['V_candidate_state'] = form_1m[contact_key]['candidate_state']

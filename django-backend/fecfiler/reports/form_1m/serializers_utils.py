# This function was separated out from the serializers.py file because
# when fecfiler.reports.form_1m.serializers is imported into the
# fecfiler.reports.serializers file, a circlular import failure is created.

def add_form_1m_contact_fields(data, representation):
    key = 'contact_affiliated'
    if data.get(key):
        representation['affiliated_committee_fec_id'] = data[key]['committee_id']
        representation['affiliated_committee_name'] = data[key]['name']

    key = 'contact_candidate_I'
    if data.get(key):
        representation['I_candidate_id_number'] = data[key]['candidate_id']
        representation['I_candidate_last_name'] = data[key]['last_name']
        representation['I_candidate_first_name'] = data[key]['first_name']
        representation['I_candidate_middle_name'] = data[key]['middle_name']
        representation['I_candidate_prefix'] = data[key]['prefix']
        representation['I_candidate_suffix'] = data[key]['suffix']
        representation['I_candidate_office'] = data[key]['candidate_office']
        representation['I_candidate_district'] = data[key]['candidate_district']
        representation['I_candidate_state'] = data[key]['candidate_state']

    key = 'contact_candidate_II'
    if data.get(key):
        representation['II_candidate_id_number'] = data[key]['candidate_id']
        representation['II_candidate_last_name'] = data[key]['last_name']
        representation['II_candidate_first_name'] = data[key]['first_name']
        representation['II_candidate_middle_name'] = data[key]['middle_name']
        representation['II_candidate_prefix'] = data[key]['prefix']
        representation['II_candidate_suffix'] = data[key]['suffix']
        representation['II_candidate_office'] = data[key]['candidate_office']
        representation['II_candidate_district'] = data[key]['candidate_district']
        representation['II_candidate_state'] = data[key]['candidate_state']

    key = 'contact_candidate_III'
    if data.get(key):
        representation['III_candidate_id_number'] = data[key]['candidate_id']
        representation['III_candidate_last_name'] = data[key]['last_name']
        representation['III_candidate_first_name'] = data[key]['first_name']
        representation['III_candidate_middle_name'] = data[key]['middle_name']
        representation['III_candidate_prefix'] = data[key]['prefix']
        representation['III_candidate_suffix'] = data[key]['suffix']
        representation['III_candidate_office'] = data[key]['candidate_office']
        representation['III_candidate_district'] = data[key]['candidate_district']
        representation['III_candidate_state'] = data[key]['candidate_state']

    key = 'contact_candidate_IV'
    if data.get(key):
        representation['IV_candidate_id_number'] = data[key]['candidate_id']
        representation['IV_candidate_last_name'] = data[key]['last_name']
        representation['IV_candidate_first_name'] = data[key]['first_name']
        representation['IV_candidate_middle_name'] = data[key]['middle_name']
        representation['IV_candidate_prefix'] = data[key]['prefix']
        representation['IV_candidate_suffix'] = data[key]['suffix']
        representation['IV_candidate_office'] = data[key]['candidate_office']
        representation['IV_candidate_district'] = data[key]['candidate_district']
        representation['IV_candidate_state'] = data[key]['candidate_state']

    key = 'contact_candidate_V'
    if data.get(key):
        representation['V_candidate_id_number'] = data[key]['candidate_id']
        representation['V_candidate_last_name'] = data[key]['last_name']
        representation['V_candidate_first_name'] = data[key]['first_name']
        representation['V_candidate_middle_name'] = data[key]['middle_name']
        representation['V_candidate_prefix'] = data[key]['prefix']
        representation['V_candidate_suffix'] = data[key]['suffix']
        representation['V_candidate_office'] = data[key]['candidate_office']
        representation['V_candidate_district'] = data[key]['candidate_district']
        representation['V_candidate_state'] = data[key]['candidate_state']

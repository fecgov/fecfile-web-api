from fecfiler.shared.utilities import get_model_data
from fecfiler.reports.form_1m.models import Form1M

# This function was separated out from the serializers.py file because
# when fecfiler.reports.form_1m.serializers is imported into the
# fecfiler.reports.serializers file, a circlular import failure is created.

def add_form_1m_contact_fields(data, representation):
    if data.get('contact_affiliated'):
        representation['affiliated_committee_fec_id'] = data['contact_affiliated']['committee_id']
        representation['affiliated_committee_name'] = data['contact_affiliated']['name']
    if data.get('contact_candidate_I'):
        representation['I_candidate_id_number'] = data['contact_candidate_I']['candidate_id']
        representation['I_candidate_last_name'] = data['contact_candidate_I']['last_name']
        representation['I_candidate_first_name'] = data['contact_candidate_I']['first_name']
        representation['I_candidate_middle_name'] = data['contact_candidate_I']['middle_name']
        representation['I_candidate_prefix'] = data['contact_candidate_I']['prefix']
        representation['I_candidate_suffix'] = data['contact_candidate_I']['suffix']
        representation['I_candidate_office'] = data['contact_candidate_I']['candidate_office']
        representation['I_candidate_district'] = data['contact_candidate_I']['candidate_district']
        representation['I_candidate_state'] = data['contact_candidate_I']['candidate_state']
    if data.get('contact_candidate_II'):
        representation['II_candidate_id_number'] = data['contact_candidate_II']['candidate_id']
        representation['II_candidate_last_name'] = data['contact_candidate_II']['last_name']
        representation['II_candidate_first_name'] = data['contact_candidate_II']['first_name']
        representation['II_candidate_middle_name'] = data['contact_candidate_II']['middle_name']
        representation['II_candidate_prefix'] = data['contact_candidate_II']['prefix']
        representation['II_candidate_suffix'] = data['contact_candidate_II']['suffix']
        representation['II_candidate_office'] = data['contact_candidate_II']['candidate_office']
        representation['II_candidate_district'] = data['contact_candidate_II']['candidate_district']
        representation['II_candidate_state'] = data['contact_candidate_II']['candidate_state']
    if data.get('contact_candidate_III'):
        representation['III_candidate_id_number'] = data['contact_candidate_III']['candidate_id']
        representation['III_candidate_last_name'] = data['contact_candidate_III']['last_name']
        representation['III_candidate_first_name'] = data['contact_candidate_III']['first_name']
        representation['III_candidate_middle_name'] = data['contact_candidate_III']['middle_name']
        representation['III_candidate_prefix'] = data['contact_candidate_III']['prefix']
        representation['III_candidate_suffix'] = data['contact_candidate_III']['suffix']
        representation['III_candidate_office'] = data['contact_candidate_III']['candidate_office']
        representation['III_candidate_district'] = data['contact_candidate_III']['candidate_district']
        representation['III_candidate_state'] = data['contact_candidate_III']['candidate_state']
    if data.get('contact_candidate_IV'):
        representation['IV_candidate_id_number'] = data['contact_candidate_IV']['candidate_id']
        representation['IV_candidate_last_name'] = data['contact_candidate_IV']['last_name']
        representation['IV_candidate_first_name'] = data['contact_candidate_IV']['first_name']
        representation['IV_candidate_middle_name'] = data['contact_candidate_IV']['middle_name']
        representation['IV_candidate_prefix'] = data['contact_candidate_IV']['prefix']
        representation['IV_candidate_suffix'] = data['contact_candidate_IV']['suffix']
        representation['IV_candidate_office'] = data['contact_candidate_IV']['candidate_office']
        representation['IV_candidate_district'] = data['contact_candidate_IV']['candidate_district']
        representation['IV_candidate_state'] = data['contact_candidate_IV']['candidate_state']
    if data.get('contact_candidate_V'):
        representation['V_candidate_id_number'] = data['contact_candidate_V']['candidate_id']
        representation['V_candidate_last_name'] = data['contact_candidate_V']['last_name']
        representation['V_candidate_first_name'] = data['contact_candidate_V']['first_name']
        representation['V_candidate_middle_name'] = data['contact_candidate_V']['middle_name']
        representation['V_candidate_prefix'] = data['contact_candidate_V']['prefix']
        representation['V_candidate_suffix'] = data['contact_candidate_V']['suffix']
        representation['V_candidate_office'] = data['contact_candidate_V']['candidate_office']
        representation['V_candidate_district'] = data['contact_candidate_V']['candidate_district']
        representation['V_candidate_state'] = data['contact_candidate_V']['candidate_state']

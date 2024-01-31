# For these transaction types, the payee committee is used for the beneficiary committee.
BENEFICIARY_COMMITTEE_USE_DONOR_TYPES = [
    'TRANSFER_TO_AFFILIATES',
    'CONTRIBUTION_TO_CANDIDATE',
    'CONTRIBUTION_TO_CANDIDATE_VOID',
    'CONTRIBUTION_TO_OTHER_COMMITTEE',
    'CONTRIBUTION_TO_OTHER_COMMITTEE_VOID',
    'INDIVIDUAL_REFUND_NON_CONTRIBUTION_ACCOUNT',
    'BUSINESS_LABOR_REFUND_NON_CONTRIBUTION_ACCOUNT',
    'OTHER_COMMITTEE_REFUND_NON_CONTRIBUTION_ACCOUNT',
    'OTHER_COMMITTEE_REFUND_REFUND_NP_HEADQUARTERS_ACCOUNT',
    'OTHER_COMMITTEE_REFUND_REFUND_NP_CONVENTION_ACCOUNT',
    'OTHER_COMMITTEE_REFUND_REFUND_NP_RECOUNT_ACCOUNT',
    'REFUND_PARTY_CONTRIBUTION',
    'REFUND_PARTY_CONTRIBUTION_VOID',
    'REFUND_PAC_CONTRIBUTION',
    'REFUND_PAC_CONTRIBUTION_VOID',
    'CONDUIT_EARMARK_OUT_DEPOSITED',
    'CONDUIT_EARMARK_OUT_UNDEPOSITED',
    'PAC_CONDUIT_EARMARK_OUT_DEPOSITED',
    'PAC_CONDUIT_EARMARK_OUT_UNDEPOSITED',
    'LOAN_MADE',
    'PAC_IN_KIND_OUT',
    'PARTY_IN_KIND_OUT',
    'IN_KIND_TRANSFER_OUT',
    'IN_KIND_TRANSFER_FEA_OUT',
]


def add_schedule_b_contact_fields(instance, representation=None):
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
        data['payee_employer'] = instance.contact_1.employer
        data['payee_occupation'] = instance.contact_1.occupation
        if instance.transaction_type_identifier in BENEFICIARY_COMMITTEE_USE_DONOR_TYPES:
            data['beneficiary_committee_name'] = instance.contact_1.name
            data['beneficiary_committee_fec_id'] = instance.contact_1.committee_id
    if instance.contact_2:
        data['beneficiary_candidate_first_name'] = instance.contact_2.first_name
        data['beneficiary_candidate_last_name'] = instance.contact_2.last_name
        data['beneficiary_candidate_middle_name'] = (
            instance.contact_2.middle_name
        )
        data['beneficiary_candidate_prefix'] = instance.contact_2.prefix
        data['beneficiary_candidate_suffix'] = instance.contact_2.suffix
        data['beneficiary_candidate_fec_id'] = instance.contact_2.candidate_id
        data['beneficiary_candidate_office'] = (
            instance.contact_2.candidate_office
        )
        data['beneficiary_candidate_state'] = instance.contact_2.candidate_state
        data['beneficiary_candidate_district'] = (
            instance.contact_2.candidate_district
        )
    if instance.contact_3:
        data['beneficiary_committee_name'] = instance.contact_3.name
        data['beneficiary_committee_fec_id'] = instance.contact_3.committee_id

    if representation:
        representation.update(data)
    else:
        for (k, v) in data.items():
            setattr(instance, k, v)

# For these transaction types, the contributor committee is used for the donor committee.
DONOR_COMMITTEE_USE_CONTRIBUTOR_TYPES = [
    'EARMARK_MEMO',
    'PARTY_RECEIPT',
    'PARTY_RETURN',
    'PARTY_IN_KIND_RECEIPT',
    'PAC_IN_KIND_RECEIPT',
    'IN_KIND_TRANSFER',
    'IN_KIND_TRANSFER_FEDERAL_ELECTION_ACTIVITY',
    'PAC_RECEIPT',
    'PAC_EARMARK_RECEIPT',
    'PAC_CONDUIT_EARMARK_RECEIPT_DEPOSITED',
    'PAC_CONDUIT_EARMARK_RECEIPT_UNDEPOSITED',
    'PAC_EARMARK_MEMO',
    'PAC_RETURN',
    'TRANSFER',
    'JOINT_FUNDRAISING_TRANSFER',
    'PARTY_JF_TRANSFER_MEMO',
    'PAC_JF_TRANSFER_MEMO',
    'JF_TRANSFER_NATIONAL_PARTY_RECOUNT_ACCOUNT',
    'PAC_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO',
    'JF_TRANSFER_NATIONAL_PARTY_CONVENTION_ACCOUNT',
    'PAC_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO',
    'JF_TRANSFER_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT',
    'PAC_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO',
    'REFUND_TO_FEDERAL_CANDIDATE',
    'REFUND_TO_OTHER_POLITICAL_COMMITTEE',
    'OTHER_COMMITTEE_NON_CONTRIBUTION_ACCOUNT',
    'PARTY_RECOUNT_RECEIPT',
    'PAC_RECOUNT_RECEIPT',
    'PARTY_NATIONAL_PARTY_RECOUNT_ACCOUNT',
    'PAC_NATIONAL_PARTY_RECOUNT_ACCOUNT',
    'PARTY_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT',
    'PAC_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT',
    'PARTY_NATIONAL_PARTY_CONVENTION_ACCOUNT',
    'PAC_NATIONAL_PARTY_CONVENTION_ACCOUNT',
    'EARMARK_MEMO_RECOUNT_ACCOUNT',
    'EARMARK_MEMO_CONVENTION_ACCOUNT',
    'EARMARK_MEMO_HEADQUARTERS_ACCOUNT',
]


def add_schedule_a_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        data['contributor_organization_name'] = instance.contact_1.name
        data['contributor_last_name'] = instance.contact_1.last_name
        data['contributor_first_name'] = instance.contact_1.first_name
        data['contributor_middle_name'] = instance.contact_1.middle_name
        data['contributor_prefix'] = instance.contact_1.prefix
        data['contributor_suffix'] = instance.contact_1.suffix
        data['contributor_street_1'] = instance.contact_1.street_1
        data['contributor_street_2'] = instance.contact_1.street_2
        data['contributor_city'] = instance.contact_1.city
        data['contributor_state'] = instance.contact_1.state
        data['contributor_zip'] = instance.contact_1.zip
        data['contributor_employer'] = instance.contact_1.employer
        data['contributor_occupation'] = instance.contact_1.occupation
        if instance.transaction_type_identifier in DONOR_COMMITTEE_USE_CONTRIBUTOR_TYPES:
            data['donor_committee_name'] = instance.contact_1.name
            data['donor_committee_fec_id'] = instance.contact_1.committee_id
    if instance.contact_2:
        data['donor_candidate_fec_id'] = instance.contact_2.candidate_id
        data['donor_candidate_last_name'] = instance.contact_2.last_name
        data['donor_candidate_first_name'] = instance.contact_2.first_name
        data['donor_candidate_middle_name'] = instance.contact_2.middle_name
        data['donor_candidate_prefix'] = instance.contact_2.prefix
        data['donor_candidate_suffix'] = instance.contact_2.suffix
        data['donor_candidate_office'] = instance.contact_2.candidate_office
        data['donor_candidate_state'] = instance.contact_2.candidate_state
        data['donor_candidate_district'] = instance.contact_2.candidate_district
    if instance.contact_3:
        data['donor_committee_name'] = instance.contact_3.name
        data['donor_committee_fec_id'] = instance.contact_3.committee_id

    if representation:
        representation.update(data)
    else:
        for (k, v) in data.items():
            setattr(instance, k, v)
        
# For these transaction types, the payee committee is used for the beneficiary committee.
from ..utils import add_org_ind_contact, add_candidate_contact

BENEFICIARY_COMMITTEE_USE_DONOR_TYPES = [
    "TRANSFER_TO_AFFILIATES",
    "CONTRIBUTION_TO_CANDIDATE",
    "CONTRIBUTION_TO_CANDIDATE_VOID",
    "CONTRIBUTION_TO_OTHER_COMMITTEE",
    "CONTRIBUTION_TO_OTHER_COMMITTEE_VOID",
    "INDIVIDUAL_REFUND_NON_CONTRIBUTION_ACCOUNT",
    "BUSINESS_LABOR_REFUND_NON_CONTRIBUTION_ACCOUNT",
    "OTHER_COMMITTEE_REFUND_NON_CONTRIBUTION_ACCOUNT",
    "OTHER_COMMITTEE_REFUND_REFUND_NP_HEADQUARTERS_ACCOUNT",
    "OTHER_COMMITTEE_REFUND_REFUND_NP_CONVENTION_ACCOUNT",
    "OTHER_COMMITTEE_REFUND_REFUND_NP_RECOUNT_ACCOUNT",
    "REFUND_PARTY_CONTRIBUTION",
    "REFUND_PARTY_CONTRIBUTION_VOID",
    "REFUND_PAC_CONTRIBUTION",
    "REFUND_PAC_CONTRIBUTION_VOID",
    "CONDUIT_EARMARK_OUT_DEPOSITED",
    "CONDUIT_EARMARK_OUT_UNDEPOSITED",
    "PAC_CONDUIT_EARMARK_OUT_DEPOSITED",
    "PAC_CONDUIT_EARMARK_OUT_UNDEPOSITED",
    "LOAN_MADE",
    "PAC_IN_KIND_OUT",
    "PARTY_IN_KIND_OUT",
    "IN_KIND_TRANSFER_OUT",
    "IN_KIND_TRANSFER_FEA_OUT",
]


def add_schedule_b_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        add_org_ind_contact(data, instance.contact_1, "payee")
        data["payee_employer"] = instance.contact_1.employer
        data["payee_occupation"] = instance.contact_1.occupation
        if instance.transaction_type_identifier in BENEFICIARY_COMMITTEE_USE_DONOR_TYPES:
            data["beneficiary_committee_name"] = instance.contact_1.name
            data["beneficiary_committee_fec_id"] = instance.contact_1.committee_id
    if instance.contact_2:
        add_candidate_contact(data, instance.contact_2, "beneficiary", True)
    if instance.contact_3:
        data["beneficiary_committee_name"] = instance.contact_3.name
        data["beneficiary_committee_fec_id"] = instance.contact_3.committee_id

    if representation:
        representation.update(data)
    else:
        for k, v in data.items():
            setattr(instance, k, v)

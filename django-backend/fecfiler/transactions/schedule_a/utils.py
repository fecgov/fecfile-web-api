# For these transaction types, the contributor committee is used for the donor committee.
from ..utils import add_org_ind_contact, add_candidate_contact
from fecfiler.transactions.models import Transaction

DONOR_COMMITTEE_USE_CONTRIBUTOR_TYPES = [
    "EARMARK_MEMO",
    "PARTY_RECEIPT",
    "PARTY_RETURN",
    "PARTY_IN_KIND_RECEIPT",
    "PAC_IN_KIND_RECEIPT",
    "IN_KIND_TRANSFER",
    "IN_KIND_TRANSFER_FEDERAL_ELECTION_ACTIVITY",
    "PAC_RECEIPT",
    "PAC_EARMARK_RECEIPT",
    "PAC_CONDUIT_EARMARK_RECEIPT_DEPOSITED",
    "PAC_CONDUIT_EARMARK_RECEIPT_UNDEPOSITED",
    "PAC_EARMARK_MEMO",
    "PAC_RETURN",
    "TRANSFER",
    "JOINT_FUNDRAISING_TRANSFER",
    "PARTY_JF_TRANSFER_MEMO",
    "PAC_JF_TRANSFER_MEMO",
    "JF_TRANSFER_NATIONAL_PARTY_RECOUNT_ACCOUNT",
    "PAC_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO",
    "JF_TRANSFER_NATIONAL_PARTY_CONVENTION_ACCOUNT",
    "PAC_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO",
    "JF_TRANSFER_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT",
    "PAC_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO",
    "REFUND_TO_FEDERAL_CANDIDATE",
    "REFUND_TO_OTHER_POLITICAL_COMMITTEE",
    "OTHER_COMMITTEE_NON_CONTRIBUTION_ACCOUNT",
    "PARTY_RECOUNT_RECEIPT",
    "PAC_RECOUNT_RECEIPT",
    "PARTY_NATIONAL_PARTY_RECOUNT_ACCOUNT",
    "PAC_NATIONAL_PARTY_RECOUNT_ACCOUNT",
    "PARTY_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT",
    "PAC_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT",
    "PARTY_NATIONAL_PARTY_CONVENTION_ACCOUNT",
    "PAC_NATIONAL_PARTY_CONVENTION_ACCOUNT",
    "EARMARK_MEMO_RECOUNT_ACCOUNT",
    "EARMARK_MEMO_CONVENTION_ACCOUNT",
    "EARMARK_MEMO_HEADQUARTERS_ACCOUNT",
]


def add_schedule_a_contact_fields(instance: Transaction, representation: dict = None):
    data = {}
    if instance.contact_1:
        add_org_ind_contact(data, instance.contact_1, "contributor")
        data["contributor_employer"] = instance.contact_1.employer
        data["contributor_occupation"] = instance.contact_1.occupation
        if instance.transaction_type_identifier in DONOR_COMMITTEE_USE_CONTRIBUTOR_TYPES:
            data["donor_committee_name"] = instance.contact_1.name
            data["donor_committee_fec_id"] = instance.contact_1.committee_id
    if instance.contact_2:
        add_candidate_contact(data, instance.contact_2, "donor", True)
    if instance.contact_3:
        data["donor_committee_name"] = instance.contact_3.name
        data["donor_committee_fec_id"] = instance.contact_3.committee_id

    if representation:
        representation.update(data)
    else:
        for k, v in data.items():
            setattr(instance, k, v)

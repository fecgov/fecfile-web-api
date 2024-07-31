from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.models import Transaction
from django.db.models import Value, Case, When, F, Q


def update_dependent_descriptions(transaction: Transaction):
    """Joint Fundraising Transfer committee names must be updated in the contribution_purpose_descrip field of
    dependent transactions."""
    if transaction.transaction_type_identifier in JF_TRANSFER_DEPENDENCIES:
        dependencies = JF_TRANSFER_DEPENDENCIES[transaction.transaction_type_identifier]
        dependents = ScheduleA.objects.filter(
            Q(
                transaction__parent_transaction_id=transaction.id,
                transaction__transaction_type_identifier__in=dependencies["children"],
            )
            | Q(
                transaction__parent_transaction__parent_transaction_id=transaction.id,
                transaction__transaction_type_identifier__in=dependencies[
                    "grandchildren"
                ],
            )
        )
        update_expression = get_update_expression(transaction)
        dependents.update(contribution_purpose_descrip=Value(update_expression))


def get_jf_transfer_description(
    memo_prefix: str, committee_name: str, is_attribution: bool
):
    """Generate a description for the dependent transaction of a joint fundraising transfer.
    If it's an attribution, the description will include a parenthetical indicating that it's a partnership attribution.
    """
    committee_clause = f"{memo_prefix} {committee_name}"
    if is_attribution:
        parenthetical = "(Partnership Attribution)"
        if len(committee_clause + parenthetical) > 100:
            committee_clause = committee_clause[: 97 - len(parenthetical)] + "..."
        return f"{committee_clause} {parenthetical}"
    return committee_clause


def get_update_expression(transaction: Transaction):
    """Get the update expression for the dependent transaction descriptions.
    The children will have different descriptions than the grandchildren.
    """
    dependencies = JF_TRANSFER_DEPENDENCIES[transaction.transaction_type_identifier]
    children = dependencies["children"]
    child_update = get_jf_transfer_description(
        dependencies["prefix"], transaction.committee_name, False
    )
    grandchildren = dependencies["grandchildren"]
    grandchild_update = get_jf_transfer_description(
        dependencies["prefix"], transaction.committee_name, True
    )
    return Case(
        When(
            transaction__transaction_type_identifier__in=children,
            then=Value(child_update),
        ),
        When(
            transaction__transaction_type_identifier__in=grandchildren,
            then=Value(grandchild_update),
        ),
        default=F("contribution_purpose_descrip"),
    )


# Dictionary of joint fundraising transfer dependencies.
# Each key is a transaction type identifier that has dependent transactions.
# The prefix is the same across all dependent transactions.
# Specifies grandchildren because their description includes a parenthetical.
JF_TRANSFER_DEPENDENCIES = {
    "JOINT_FUNDRAISING_TRANSFER": {
        "prefix": "JF Memo:",
        "children": [
            "INDIVIDUAL_JF_TRANSFER_MEMO",
            "PAC_JF_TRANSFER_MEMO",
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            "PARTY_JF_TRANSFER_MEMO",
            "TRIBAL_JF_TRANSFER_MEMO",
        ],
        "grandchildren": ["PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO"],
    },
    "JF_TRANSFER_NATIONAL_PARTY_CONVENTION_ACCOUNT": {
        "prefix": "Pres. Nominating Convention Account JF Memo:",
        "children": [
            "INDIVIDUAL_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO",
            "PAC_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO",
            "PARTNERSHIP_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO",
            "TRIBAL_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO",
        ],
        "grandchildren": [
            "PARTNERSHIP_ATTRIBUTION_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO"
        ],
    },
    "JF_TRANSFER_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT": {
        "prefix": "Headquarters Buildings Account JF Memo:",
        "children": [
            "INDIVIDUAL_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO",
            "PAC_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO",
            "PARTNERSHIP_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO",
            "TRIBAL_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO",
        ],
        "grandchildren": [
            "PARTNERSHIP_ATTRIBUTION_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO"
        ],
    },
    "JF_TRANSFER_NATIONAL_PARTY_RECOUNT_ACCOUNT": {
        "prefix": "Recount/Legal Proceedings Account JF Memo:",
        "children": [
            "INDIVIDUAL_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO",
            "PAC_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO",
            "PARTNERSHIP_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO",
            "TRIBAL_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO",
        ],
        "grandchildren": [
            "PARTNERSHIP_ATTRIBUTION_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO"
        ],
    },
}

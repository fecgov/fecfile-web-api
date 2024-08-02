from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.models import Transaction
from django.db.models import Value, Case, When, F, Q, Subquery, OuterRef
import structlog

logger = structlog.get_logger(__name__)


def update_dependent_descriptions(transaction: Transaction):
    """Joint Fundraising Transfer committee names must be updated in the contribution_purpose_descrip field of
    dependent transactions."""
    if transaction.transaction_type_identifier in JF_TRANSFER_DEPENDENCIES:
        dependencies = JF_TRANSFER_DEPENDENCIES[transaction.transaction_type_identifier]

        """Identify the transaction types to update"""
        children = dependencies["children"]
        grandchildren = dependencies["grandchildren"]

        """The description for all children will be the same,
            and the description for all grandchildren will be the same."""
        child_update = get_jf_transfer_description(
            dependencies["prefix"], transaction.contact_1.name, False
        )
        grandchild_update = get_jf_transfer_description(
            dependencies["prefix"], transaction.contact_1.name, True
        )

        """Establish the queryset with all dependent transactions"""
        dependents = ScheduleA.objects.filter(
            Q(
                transaction__parent_transaction_id=transaction.id,
                transaction__transaction_type_identifier__in=children,
            )
            | Q(
                transaction__parent_transaction__parent_transaction_id=transaction.id,
                transaction__transaction_type_identifier__in=grandchildren,
            )
        )

        """Update the contribution_purpose_descrip field for all dependent transactions.
            Django does not support Case(When()) where the condition using joined tables (transaction__).
            So we use a Subquery to define the new description
            Ref: https://code.djangoproject.com/ticket/14104"""
        count = dependents.update(
            contribution_purpose_descrip=Subquery(
                ScheduleA.objects.filter(id=OuterRef("id"))
                .annotate(
                    new_description=Case(
                        When(
                            transaction__parent_transaction_id=transaction.id,
                            then=Value(child_update),
                        ),
                        default=Value(grandchild_update),
                    )
                )
                .values("new_description")[:1]
            ),
        )
        logger.debug(f"Updated {count} dependent transactions for {transaction}")


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
            committee_clause = committee_clause[: 96 - len(parenthetical)] + "..."
        return f"{committee_clause} {parenthetical}"
    return committee_clause


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

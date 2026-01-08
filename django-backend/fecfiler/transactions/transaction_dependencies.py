from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.models import Transaction
from django.db.models import Value, Case, When, Q, Subquery, OuterRef, Exists
import structlog

logger = structlog.get_logger(__name__)


def update_dependent_children(transaction: Transaction):
    """Joint Fundraising Transfer committee names must be updated
    in the contribution_purpose_descrip field of dependent transactions."""
    if transaction.transaction_type_identifier in JF_TRANSFER_DEPENDENCIES:
        dependencies = JF_TRANSFER_DEPENDENCIES[transaction.transaction_type_identifier]

        """Identify the transaction types to update"""
        children = dependencies["children"]
        grandchildren = dependencies["grandchildren"]

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
        Django does not support Case(When()) where the condition using
        joined tables (transaction__). So we use a Subquery to define
        the new description

        Ref: https://code.djangoproject.com/ticket/14104"""
        count = dependents.update(
            contribution_purpose_descrip=Subquery(
                ScheduleA.objects.filter(id=OuterRef("id"))
                .annotate(
                    new_description=get_new_description_clause(
                        dependencies["prefix"], transaction.contact_1.name, transaction.id
                    )
                )
                .values("new_description")[:1]
            ),
        )
        logger.debug(f"Updated {count} dependent transactions for {transaction}")


def update_dependent_parent(transaction: Transaction):
    """Update the contribution_purpose_descrip field for PARTNERSHIP_MEMO transactions
    when thier children are created or deleted."""
    if transaction.transaction_type_identifier in PARTNERSHIP_ATTRIBUTIONS:
        parent = transaction.parent_transaction
        grandparent = parent.parent_transaction
        dependencies = JF_TRANSFER_DEPENDENCIES[grandparent.transaction_type_identifier]
        _, _, partnership_no_children_update, partnership_with_children_update = (
            get_jf_transfer_descriptions(
                dependencies["prefix"], grandparent.contact_1.name
            )
        )

        ScheduleA.objects.filter(transaction__id=parent.id).update(
            contribution_purpose_descrip=Subquery(
                ScheduleA.objects.filter(id=OuterRef("id"))
                .annotate(
                    new_description=Case(
                        When(HAS_CHILDREN, then=Value(partnership_with_children_update)),
                        default=Value(partnership_no_children_update),
                    )
                )
                .values("new_description")[:1]
            )
        )


def get_new_description_clause(
    memo_prefix: str, commmittee_name: str, transaction_id: str
):
    """Generate Django Expression to update the contribution_purpose_descrip field"""

    """Create descriptions to be used by different dependents."""
    (
        child_update,
        attribution_update,
        partnership_no_children_update,
        partnership_with_children_update,
    ) = get_jf_transfer_descriptions(memo_prefix, commmittee_name)

    partnership_case = Case(
        When(HAS_CHILDREN, then=Value(partnership_with_children_update)),
        default=Value(partnership_no_children_update),
    )
    child_case = Case(
        When(
            transaction__transaction_type_identifier__in=PARTNERSHIP_MEMOS,
            then=partnership_case,
        ),
        default=Value(child_update),
    )
    return Case(
        When(
            transaction__parent_transaction_id=transaction_id,
            then=child_case,
        ),
        default=Value(attribution_update),
    )


def get_jf_transfer_descriptions(memo_prefix: str, commmittee_name: str):
    """Generate descriptions for the dependent transactions of a joint
    fundraising transfer. There are 4 descriptions:
    1. The description for most children transactions (ex: "JF Memo: Committee Name")
    2. The description for grandchildren transactions
        (ex: "JF Memo: Committee Name (Partnership Attribution)")
    3. The description for partnership memos with no grandchildren
        (ex: "JF Memo: Committee Name (Partnership attributions do not meet
          itemization threshold)")
    4. The description for partnership memos with grandchildren
        (ex: "JF Memo: Committee Name (See Partnership Attribution(s) below)")
    """
    committee_clause = f"{memo_prefix} {commmittee_name}"
    attribution_description = get_truncated_description(
        committee_clause, "(Partnership Attribution)"
    )
    partnership_description_no_children = get_truncated_description(
        committee_clause, "(Partnership attributions do not meet itemization threshold)"
    )
    partnership_description_with_children = get_truncated_description(
        committee_clause, "(See Partnership Attribution(s) below)"
    )

    return (
        committee_clause,
        attribution_description,
        partnership_description_no_children,
        partnership_description_with_children,
    )


def get_truncated_description(description: str, parenthetical: str):
    """Truncate the description to fit within the 100 character limit
    and append a parenthetical."""
    if len(description + parenthetical) > 100:
        description = description[: 96 - len(parenthetical)] + "..."
    return f"{description} {parenthetical}"


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

# List of transaction types that are partnership memos.
PARTNERSHIP_MEMOS = [
    "PARTNERSHIP_JF_TRANSFER_MEMO",
    "PARTNERSHIP_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO",
    "PARTNERSHIP_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO",
    "PARTNERSHIP_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO",
]

# List of transaction types that are partnership attributions.
PARTNERSHIP_ATTRIBUTIONS = [
    "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
    "PARTNERSHIP_ATTRIBUTION_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO",
    "PARTNERSHIP_ATTRIBUTION_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO",
    "PARTNERSHIP_ATTRIBUTION_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO",
]

# Subquery to check if a transaction has children.
HAS_CHILDREN = Exists(
    Transaction.objects.filter(parent_transaction=OuterRef("transaction__id")).values(
        "id"
    )[:1]
)

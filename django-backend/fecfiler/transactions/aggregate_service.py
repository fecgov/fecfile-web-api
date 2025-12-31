"""
Service module for calculating and updating transaction aggregates.

This module handles the calculation of aggregates for Schedule A and Schedule B
transactions that are grouped by entity (contact, calendar year, and aggregation group),
as well as aggregates for Schedule E transactions grouped by election office.

Previously, these calculations were handled by database triggers. This service moves
that logic into Django code for better maintainability and testability.
"""

from decimal import Decimal
from django.db.models import Q, F, Case, When, Sum, DecimalField, Value
from django.db import transaction as db_transaction
from .models import Transaction
from .managers import Schedule
import structlog

logger = structlog.get_logger(__name__)


def calculate_entity_aggregates(
    contact_1_id, year, aggregation_group, committee_account_id
):
    """
    Calculate and update aggregate values for Schedule A/B transactions.

    Aggregates are calculated as a running sum of effective amounts for all
    transactions matching the given entity (contact, calendar year, aggregation group),
    ordered by date and creation time.

    Args:
        contact_1_id: UUID of the contact (entity)
        year: Calendar year for aggregation
        aggregation_group: Aggregation group identifier
        committee_account_id: UUID of the committee account (for logging)

    Returns:
        Number of transactions updated
    """
    # Get all matching transactions ordered by date and created
    # Exclude force_unaggregated transactions as they don't participate in aggregation
    transactions = (
        Transaction.objects.filter(
            contact_1_id=contact_1_id,
            date__year=year,
            aggregation_group=aggregation_group,
            deleted__isnull=True,
            schedule_a__isnull=False,
            force_unaggregated__isnull=True,
        )
        | Transaction.objects.filter(
            contact_1_id=contact_1_id,
            date__year=year,
            aggregation_group=aggregation_group,
            deleted__isnull=True,
            schedule_b__isnull=False,
            force_unaggregated__isnull=True,
        )
    ).order_by("date", "created").select_related(
        "schedule_a", "schedule_b"
    )

    if not transactions.exists():
        logger.debug(
            f"No transactions found for entity aggregation: "
            f"contact_1={contact_1_id}, year={year}, group={aggregation_group}"
        )
        return 0

    update_count = 0
    running_sum = Decimal(0)

    with db_transaction.atomic():
        for txn in transactions:
            # Calculate effective amount for this transaction
            effective_amount = calculate_effective_amount(txn)

            running_sum += effective_amount
            aggregate_value = running_sum

            # Update the transaction's aggregate field
            if txn.aggregate != aggregate_value:
                txn.aggregate = aggregate_value
                txn.save(update_fields=["aggregate"])
                update_count += 1

    logger.info(
        f"Updated {update_count} transactions for entity aggregation: "
        f"contact_1={contact_1_id}, year={year}, group={aggregation_group}"
    )
    return update_count


def calculate_calendar_ytd_per_election_office(
    election_code, candidate_office, candidate_state, candidate_district, year, aggregation_group, committee_account_id=None
):
    """
    Calculate and update calendar YTD aggregates for Schedule E transactions.

    Aggregates are calculated as a running sum of effective amounts for all
    Schedule E transactions matching the given election office criteria,
    ordered by date and creation time.

    Args:
        election_code: Election code identifier
        candidate_office: Candidate office (e.g., 'P', 'S', 'H')
        candidate_state: Candidate state (may be None or empty string)
        candidate_district: Candidate district (may be None or empty string)
        year: Calendar year for aggregation
        aggregation_group: Aggregation group identifier

    Returns:
        Number of transactions updated
    """
    # Handle None/empty string values for state and district
    state_filter = Q(contact_2__candidate_state=candidate_state)
    if not candidate_state:
        state_filter = Q(contact_2__candidate_state__isnull=True) | Q(
            contact_2__candidate_state=""
        )

    district_filter = Q(contact_2__candidate_district=candidate_district)
    if not candidate_district:
        district_filter = Q(contact_2__candidate_district__isnull=True) | Q(
            contact_2__candidate_district=""
        )

    # Get all matching Schedule E transactions ordered by date and created
    # Exclude force_unaggregated transactions as they don't participate in aggregation
    query_filters = {
        "schedule_e__election_code": election_code,
        "contact_2__candidate_office": candidate_office,
        "date__year": year,
        "aggregation_group": aggregation_group,
        "deleted__isnull": True,
        "schedule_e__isnull": False,
        "force_unaggregated__isnull": True,
    }
    
    # Filter by committee_account_id if provided
    if committee_account_id:
        query_filters["committee_account_id"] = committee_account_id
    
    transactions = Transaction.objects.filter(
        **query_filters
    ).filter(state_filter, district_filter).order_by("date", "created").select_related(
        "schedule_e", "contact_2"
    )

    if not transactions.exists():
        logger.debug(
            f"No transactions found for election YTD aggregation: "
            f"election_code={election_code}, office={candidate_office}, "
            f"state={candidate_state}, district={candidate_district}, year={year}"
        )
        return 0

    update_count = 0
    running_sum = Decimal(0)

    with db_transaction.atomic():
        for txn in transactions:
            # Calculate effective amount for this transaction
            effective_amount = calculate_effective_amount(txn)

            running_sum += effective_amount
            aggregate_value = running_sum

            # Update the transaction's _calendar_ytd_per_election_office field
            if txn._calendar_ytd_per_election_office != aggregate_value:
                txn._calendar_ytd_per_election_office = aggregate_value
                txn.save(update_fields=["_calendar_ytd_per_election_office"])
                update_count += 1

    logger.info(
        f"Updated {update_count} transactions for election YTD aggregation: "
        f"election_code={election_code}, office={candidate_office}, "
        f"state={candidate_state}, district={candidate_district}, year={year}"
    )
    return update_count


def calculate_effective_amount(transaction):
    """
    Calculate the effective amount for a transaction.

    The effective amount is used for aggregation calculations and differs from
    the transaction amount for certain transaction types (e.g., refunds are
    negated) and for certain schedules (e.g., Schedule C has no effective amount).

    Args:
        transaction: Transaction instance

    Returns:
        Decimal: The effective amount for aggregation
    """
    from fecfiler.transactions.schedule_b.managers import refunds as schedule_b_refunds

    # Schedule C transactions have no effective amount for aggregation
    if transaction.schedule_c_id is not None:
        return Decimal(0)

    # Get the base amount from related schedule
    amount = None
    if transaction.schedule_a_id and transaction.schedule_a:
        amount = transaction.schedule_a.contribution_amount
    elif transaction.schedule_b_id and transaction.schedule_b:
        amount = transaction.schedule_b.expenditure_amount
    elif transaction.schedule_c2_id and transaction.schedule_c2:
        amount = transaction.schedule_c2.guaranteed_amount
    elif transaction.schedule_e_id and transaction.schedule_e:
        amount = transaction.schedule_e.expenditure_amount
    elif transaction.schedule_f_id and transaction.schedule_f:
        amount = transaction.schedule_f.expenditure_amount
    elif transaction.schedule_d_id and transaction.schedule_d:
        amount = transaction.schedule_d.incurred_amount
    elif transaction.debt_id and transaction.debt and transaction.debt.schedule_d:
        amount = transaction.debt.schedule_d.incurred_amount

    # Refunds are negated
    if amount and transaction.transaction_type_identifier in schedule_b_refunds:
        amount = amount * Decimal(-1)

    return amount if amount else Decimal(0)


def calculate_loan_payment_to_date(loan_id):
    """
    Calculate the cumulative loan payment to date for a given loan.
    
    Sums all LOAN_REPAYMENT_MADE transactions associated with the loan,
    ordered by date and creation time. For carried forward loans, also includes
    repayments from the parent loan chain.
    
    Args:
        loan_id: UUID of the loan transaction
        
    Returns:
        Number of loan transactions updated (the loan itself)
    """
    from .models import Transaction
    
    # Get the loan transaction
    try:
        loan = Transaction.objects.select_related('loan', 'loan__schedule_c').get(id=loan_id, deleted__isnull=True)
    except Transaction.DoesNotExist:
        logger.warning(f"Loan transaction {loan_id} not found")
        return 0
    
    # Collect all loan IDs in the parent chain (for carried forward loans)
    # Carried forward loans reference their parent via the 'loan' field
    loan_ids = [loan_id]
    current_loan = loan
    
    # Walk up the loan chain to find the original loan
    max_depth = 10  # Prevent infinite loops
    depth = 0
    while current_loan.loan_id and depth < max_depth:
        parent_loan = current_loan.loan
        if parent_loan and parent_loan.schedule_c:
            loan_ids.append(parent_loan.id)
            current_loan = parent_loan
            depth += 1
        else:
            break
    
    # Get all loan repayment transactions for all loans in the chain
    repayments = Transaction.objects.filter(
        loan_id__in=loan_ids,
        transaction_type_identifier="LOAN_REPAYMENT_MADE",
        deleted__isnull=True,
        schedule_b__isnull=False,
    ).order_by("date", "created").select_related("schedule_b")
    
    # Calculate the cumulative payment amount
    total_payment = Decimal(0)
    for repayment in repayments:
        if repayment.schedule_b and repayment.schedule_b.expenditure_amount:
            total_payment += repayment.schedule_b.expenditure_amount
    
    # Update the loan transaction's loan_payment_to_date field
    if loan.loan_payment_to_date != total_payment:
        loan.loan_payment_to_date = total_payment
        loan.save(update_fields=["loan_payment_to_date"])
        logger.info(
            f"Updated loan_payment_to_date for loan {loan_id}: {total_payment}"
        )
        return 1
    
    return 0


def recalculate_aggregates_for_transaction(transaction_instance):
    """
    Recalculate aggregates for a transaction and any affected related transactions.

    This function determines which aggregates need to be recalculated based on the
    transaction's schedule type and then calls the appropriate aggregate calculation
    function.

    Args:
        transaction_instance: Transaction model instance
    """
    if transaction_instance.deleted:
        # Skip calculations for deleted transactions
        return

    schedule = transaction_instance.get_schedule_name()
    transaction_date = transaction_instance.get_date()

    # If there's no transaction date, we can't aggregate
    if not transaction_date:
        return

    try:
        if schedule in [Schedule.A, Schedule.B]:
            # Recalculate entity aggregates
            year = transaction_date.year if hasattr(transaction_date, 'year') else int(str(transaction_date)[:4])
            calculate_entity_aggregates(
                transaction_instance.contact_1_id,
                year,
                transaction_instance.aggregation_group,
                transaction_instance.committee_account_id,
            )
            
            # If this is a loan repayment, recalculate loan_payment_to_date for the associated loan
            if (transaction_instance.transaction_type_identifier == "LOAN_REPAYMENT_MADE" 
                and transaction_instance.loan_id):
                calculate_loan_payment_to_date(transaction_instance.loan_id)
                
        elif schedule == Schedule.E:
            # Recalculate calendar YTD per election office aggregates
            schedule_e = transaction_instance.schedule_e
            contact_2 = transaction_instance.contact_2

            if schedule_e and contact_2:
                year = transaction_date.year if hasattr(transaction_date, 'year') else int(str(transaction_date)[:4])
                calculate_calendar_ytd_per_election_office(
                    schedule_e.election_code,
                    contact_2.candidate_office,
                    contact_2.candidate_state,
                    contact_2.candidate_district,
                    year,
                    transaction_instance.aggregation_group,
                    transaction_instance.committee_account_id,
                )
    except Exception as e:
        logger.error(
            f"Error recalculating aggregates for transaction {transaction_instance.id}: {e}",
            exc_info=True,
        )
        raise


def recalculate_aggregates_for_affected_transactions(
    original_contact_1_id,
    original_year,
    original_aggregation_group,
    original_contact_2_id=None,
    original_election_code=None,
):
    """
    Recalculate aggregates for all transactions affected by changes to related grouping fields.

    When a transaction's contact, year, or aggregation group changes, the aggregates
    for both the old and new groups may need to be recalculated.

    Args:
        original_contact_1_id: Original contact 1 ID (may be None)
        original_year: Original calendar year (may be None)
        original_aggregation_group: Original aggregation group (may be None)
        original_contact_2_id: Original contact 2 ID for election office aggregates (may be None)
        original_election_code: Original election code for election office aggregates (may be None)
    """
    # Recalculate for the original grouping if provided
    if original_contact_1_id and original_year and original_aggregation_group:
        try:
            calculate_entity_aggregates(
                original_contact_1_id,
                original_year,
                original_aggregation_group,
                None,  # committee_account_id not needed here
            )
        except Exception as e:
            logger.error(
                f"Error recalculating aggregates for original entity group: {e}",
                exc_info=True,
            )

from fecfiler.reports.form_3x.models import Form3X
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from fecfiler.cash_on_hand.models import CashOnHandYearly
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from decimal import Decimal
import structlog

logger = structlog.get_logger(__name__)


def calculate_summary(report):
    form_3x: Form3X = report.form_3x

    a, b = calculate_summary_columns(report)
    # line 6a
    form_3x.L6a_cash_on_hand_jan_1_ytd = b.get("line_6a", None)
    # line 6b
    form_3x.L6b_cash_on_hand_beginning_period = a.get("line_6b", None)
    # line 6c
    form_3x.L6c_total_receipts_period = a.get("line_6c", 0)
    form_3x.L6c_total_receipts_ytd = b.get("line_6c", 0)
    # line 6d
    form_3x.L6d_subtotal_period = a.get("line_6d", None)
    form_3x.L6d_subtotal_ytd = b.get("line_6d", None)
    # line 7
    form_3x.L7_total_disbursements_period = a.get("line_7", 0)
    form_3x.L7_total_disbursements_ytd = b.get("line_7", 0)
    # line 8
    form_3x.L8_cash_on_hand_at_close_period = a.get("line_8", None)
    form_3x.L8_cash_on_hand_close_ytd = b.get("line_8", None)
    # line 9
    form_3x.L9_debts_to_period = a.get("line_9", 0)
    # line 10
    form_3x.L10_debts_by_period = a.get("line_10", 0)
    # line 11ai
    form_3x.L11ai_itemized_period = a.get("line_11ai", 0)
    form_3x.L11ai_itemized_ytd = b.get("line_11ai", 0)
    # line 11aii
    form_3x.L11aii_unitemized_period = a.get("line_11aii", 0)
    form_3x.L11aii_unitemized_ytd = b.get("line_11aii", 0)
    # line 11aiii
    form_3x.L11aiii_total_period = a.get("line_11aiii", 0)
    form_3x.L11aiii_total_ytd = b.get("line_11aiii", 0)
    # line 11b
    form_3x.L11b_political_party_committees_period = a.get("line_11b", 0)
    form_3x.L11b_political_party_committees_ytd = b.get("line_11b", 0)
    # line 11c
    form_3x.L11c_other_political_committees_pacs_period = a.get("line_11c", 0)
    form_3x.L11c_other_political_committees_pacs_ytd = b.get("line_11c", 0)
    # line 11d
    form_3x.L11d_total_contributions_period = a.get("line_11d", 0)
    form_3x.L11d_total_contributions_ytd = b.get("line_11d", 0)
    # line 12
    form_3x.L12_transfers_from_affiliated_other_party_cmtes_period = a.get(
        "line_12", 0
    )  # noqa: E501
    form_3x.L12_transfers_from_affiliated_other_party_cmtes_ytd = b.get(
        "line_12", 0
    )  # noqa: E501
    # line 13
    form_3x.L13_all_loans_received_period = a.get("line_13", 0)
    form_3x.L13_all_loans_received_ytd = b.get("line_13", 0)
    # line 14
    form_3x.L14_loan_repayments_received_period = a.get("line_14", 0)
    form_3x.L14_loan_repayments_received_ytd = b.get("line_14", 0)
    # line 15
    form_3x.L15_offsets_to_operating_expenditures_refunds_period = a.get(
        "line_15", 0
    )  # noqa: E501
    form_3x.L15_offsets_to_operating_expenditures_refunds_ytd = b.get(
        "line_15", 0
    )  # noqa: E501
    # line 16
    form_3x.L16_refunds_of_federal_contributions_period = a.get("line_16", 0)
    form_3x.L16_refunds_of_federal_contributions_ytd = b.get("line_16", 0)
    # line 17
    form_3x.L17_other_federal_receipts_dividends_period = a.get("line_17", 0)
    form_3x.L17_other_federal_receipts_dividends_ytd = b.get("line_17", 0)
    # line 18a
    form_3x.L18a_transfers_from_nonfederal_account_h3_period = a.get(
        "line_18a", 0
    )  # noqa: E501
    form_3x.L18a_transfers_from_nonfederal_account_h3_ytd = b.get(
        "line_18a", 0
    )  # noqa: E501
    # line 18b
    form_3x.L18b_transfers_from_nonfederal_levin_h5_period = a.get(
        "line_18b", 0
    )  # noqa: E501
    form_3x.L18b_transfers_from_nonfederal_levin_h5_ytd = b.get("line_18b", 0)
    # line 18c
    form_3x.L18c_total_nonfederal_transfers_18a_18b_period = a.get(
        "line_18c", 0
    )  # noqa: E501
    form_3x.L18c_total_nonfederal_transfers_18a_18b_ytd = b.get("line_18c", 0)
    # line 19
    form_3x.L19_total_receipts_period = a.get("line_19", 0)
    form_3x.L19_total_receipts_ytd = b.get("line_19", 0)
    # line 20
    form_3x.L20_total_federal_receipts_period = a.get("line_20", 0)
    form_3x.L20_total_federal_receipts_ytd = b.get("line_20", 0)
    # line 21ai
    form_3x.L21ai_federal_share_period = a.get("line_21ai", 0)
    form_3x.L21ai_federal_share_ytd = b.get("line_21ai", 0)
    # line 21aii
    form_3x.L21aii_nonfederal_share_period = a.get("line_21aii", 0)
    form_3x.L21aii_nonfederal_share_ytd = b.get("line_21aii", 0)
    # line 21b
    form_3x.L21b_other_federal_operating_expenditures_period = a.get(
        "line_21b", 0
    )  # noqa: E501
    form_3x.L21b_other_federal_operating_expenditures_ytd = b.get(
        "line_21b", 0
    )  # noqa: E501
    # line 21c
    form_3x.L21c_total_operating_expenditures_ytd = b.get("line_21c", 0)
    form_3x.L21c_total_operating_expenditures_period = a.get("line_21c", 0)
    # line 22
    form_3x.L22_transfers_to_affiliated_other_party_cmtes_period = a.get(
        "line_22", 0
    )  # noqa: E501
    form_3x.L22_transfers_to_affiliated_other_party_cmtes_ytd = b.get(
        "line_22", 0
    )  # noqa: E501
    # line 23
    form_3x.L23_contributions_to_federal_candidates_cmtes_period = a.get(
        "line_23", 0
    )  # noqa: E501
    form_3x.L23_contributions_to_federal_candidates_cmtes_ytd = b.get(
        "line_23", 0
    )  # noqa: E501
    # line 24
    form_3x.L24_independent_expenditures_period = a.get("line_24", 0)
    form_3x.L24_independent_expenditures_ytd = b.get("line_24", 0)
    # line 25
    form_3x.L25_coordinated_expend_made_by_party_cmtes_period = a.get(
        "line_25", 0
    )  # noqa: E501
    form_3x.L25_coordinated_expend_made_by_party_cmtes_ytd = b.get(
        "line_25", 0
    )  # noqa: E501
    # line 26
    form_3x.L26_loan_repayments_period = a.get("line_26", 0)
    form_3x.L26_loan_repayments_made_ytd = b.get("line_26", 0)
    # line 27
    form_3x.L27_loans_made_period = a.get("line_27", 0)
    form_3x.L27_loans_made_ytd = b.get("line_27", 0)
    # line 28a
    form_3x.L28a_individuals_persons_period = a.get("line_28a", 0)
    form_3x.L28a_individuals_persons_ytd = b.get("line_28a", 0)
    # line 28b
    form_3x.L28b_political_party_committees_period = a.get("line_28b", 0)
    form_3x.L28b_political_party_committees_ytd = b.get("line_28b", 0)
    # line 28c
    form_3x.L28c_other_political_committees_period = a.get("line_28c", 0)
    form_3x.L28c_other_political_committees_ytd = b.get("line_28c", 0)
    # line 28d
    form_3x.L28d_total_contributions_refunds_period = a.get("line_28d", 0)
    form_3x.L28d_total_contributions_refunds_ytd = b.get("line_28d", 0)
    # line 29
    form_3x.L29_other_disbursements_period = a.get("line_29", 0)
    form_3x.L29_other_disbursements_ytd = b.get("line_29", 0)
    # line 30ai
    form_3x.L30ai_shared_federal_activity_h6_fed_share_period = a.get(
        "line_30ai", 0
    )  # noqa: E501
    form_3x.L30ai_shared_federal_activity_h6_fed_share_ytd = b.get(
        "line_30ai", 0
    )  # noqa: E501
    # line 30aii
    form_3x.L30aii_shared_federal_activity_h6_nonfed_period = a.get(
        "line_30aii", 0
    )  # noqa: E501
    form_3x.L30aii_shared_federal_activity_h6_nonfed_ytd = b.get(
        "line_30aii", 0
    )  # noqa: E501
    # line 30b
    form_3x.L30b_nonallocable_fed_election_activity_period = a.get(
        "line_30b", 0
    )  # noqa: E501
    form_3x.L30b_nonallocable_fed_election_activity_ytd = b.get("line_30b", 0)
    # line 30c
    form_3x.L30c_total_federal_election_activity_period = a.get("line_30c", 0)
    form_3x.L30c_total_federal_election_activity_ytd = b.get("line_30c", 0)
    # line 31
    form_3x.L31_total_disbursements_period = a.get("line_31", 0)
    form_3x.L31_total_disbursements_ytd = b.get("line_31", 0)
    # line 32
    form_3x.L32_total_federal_disbursements_period = a.get("line_32", 0)
    form_3x.L32_total_federal_disbursements_ytd = b.get("line_32", 0)
    # line 33
    form_3x.L33_total_contributions_period = a.get("line_33", 0)
    form_3x.L33_total_contributions_ytd = b.get("line_33", 0)
    # line 34
    form_3x.L34_total_contribution_refunds_period = a.get("line_34", 0)
    form_3x.L34_total_contribution_refunds_ytd = b.get("line_34", 0)
    # line 35
    form_3x.L35_net_contributions_period = a.get("line_35", 0)
    form_3x.L35_net_contributions_ytd = b.get("line_35", 0)
    # line 36
    form_3x.L36_total_federal_operating_expenditures_period = a.get(
        "line_36", 0
    )  # noqa: E501
    form_3x.L36_total_federal_operating_expenditures_ytd = b.get("line_36", 0)
    # line 37
    form_3x.L37_offsets_to_operating_expenditures_period = a.get("line_37", 0)
    form_3x.L37_offsets_to_operating_expenditures_ytd = b.get("line_37", 0)
    # line 38
    form_3x.L38_net_operating_expenditures_period = a.get("line_38", 0)
    form_3x.L38_net_operating_expenditures_ytd = b.get("line_38", 0)

    form_3x.save()


def calculate_summary_columns(report):
    column_a = calculate_summary_column_a(report)
    column_b = calculate_summary_column_b(report)

    column_a, column_b = calculate_cash_on_hand_fields(report, column_a, column_b)

    return column_a, column_b


def calculate_summary_column_a(report):

    report_transactions = Transaction.objects.transaction_view().filter(
        reports__id=report.id,
        committee_account__id=report.committee_account.id,
    )
    column_a = report_transactions.aggregate(
        line_11ai=get_line("SA11AI"),
        line_11aii=get_line("SA11AII"),
        line_11b=get_line("SA11B"),
        line_11c=get_line("SA11C"),
        line_12=get_line("SA12"),
        line_13=get_line("SA13"),
        line_14=get_line("SA14"),
        line_15=get_line("SA15"),
        line_16=get_line("SA16"),
        line_17=get_line("SA17"),
        line_21b=get_line("SB21B"),
        line_22=get_line("SB22"),
        line_23=get_line("SB23"),
        line_24=get_line("SE"),
        line_25=get_line("SF"),
        line_26=get_line("SB26"),
        line_27=get_line("SB27"),
        line_28a=get_line("SB28A"),
        line_28b=get_line("SB28B"),
        line_28c=get_line("SB28C"),
        line_29=get_line("SB29"),
        line_30b=get_line("SB30B"),
        # Temporary aggregations
        temp_sc9=get_line("SC/9", field="loan_balance"),
        temp_sd9=get_line("SD9", field="balance_at_close"),
        temp_sc10=get_line("SC/10", field="loan_balance"),
        temp_sd10=get_line("SD10", field="balance_at_close"),
    )

    column_a["line_9"] = column_a["temp_sc9"] + column_a["temp_sd9"]
    column_a["line_10"] = column_a["temp_sc10"] + column_a["temp_sd10"]
    column_a["line_11aiii"] = column_a["line_11ai"] + column_a["line_11aii"]
    column_a["line_11d"] = (
        column_a["line_11aiii"] + column_a["line_11b"] + column_a["line_11c"]
    )
    column_a["line_18c"] = Decimal(0)  # Stubbed out until a future ticket
    column_a["line_21ai"] = Decimal(0)  # Stubbed out until a future ticket
    column_a["line_21aii"] = Decimal(0)  # Stubbed out until a future ticket
    column_a["line_21c"] = (
        column_a["line_21ai"] + column_a["line_21aii"] + column_a["line_21b"]
    )
    column_a["line_28d"] = (
        column_a["line_28a"] + column_a["line_28b"] + column_a["line_28c"]
    )
    column_a["line_30ai"] = Decimal(0)  # Stubbed out until a future ticket
    column_a["line_30aii"] = Decimal(0)  # Stubbed out until a future ticket
    column_a["line_30c"] = (
        column_a["line_30ai"] + column_a["line_30aii"] + column_a["line_30b"]
    )
    column_a["line_31"] = (
        column_a["line_21c"]
        + column_a["line_22"]
        + column_a["line_23"]
        + column_a["line_24"]
        + column_a["line_25"]
        + column_a["line_26"]
        + column_a["line_27"]
        + column_a["line_28d"]
        + column_a["line_29"]
        + column_a["line_30c"]
    )
    column_a["line_32"] = (
        column_a["line_31"] - column_a["line_21aii"] - column_a["line_30aii"]
    )
    column_a["line_33"] = column_a["line_11d"]
    column_a["line_34"] = column_a["line_28d"]
    column_a["line_35"] = column_a["line_33"] - column_a["line_34"]
    column_a["line_36"] = column_a["line_21ai"] + column_a["line_21b"]
    column_a["line_37"] = column_a["line_15"]
    column_a["line_38"] = column_a["line_36"] - column_a["line_37"]
    column_a["line_6c"] = (
        column_a["line_11d"]
        + column_a["line_12"]
        + column_a["line_13"]
        + column_a["line_14"]
        + column_a["line_15"]
        + column_a["line_16"]
        + column_a["line_17"]
        + column_a["line_18c"]
    )
    column_a["line_7"] = column_a["line_31"]
    column_a["line_19"] = column_a["line_6c"]
    column_a["line_20"] = column_a["line_19"] - column_a["line_18c"]

    # Remove temporary aggregations to clean up the summary
    for key in list(column_a.keys()):
        if key.startswith("temp_"):
            column_a.pop(key)

    return column_a


def calculate_summary_column_b(report):
    committee = report.committee_account
    report_date = report.coverage_through_date
    report_year = report_date.year

    ytd_transactions = Transaction.objects.transaction_view().filter(
        committee_account=committee,
        date__year=report_year,
        date__lte=report_date,
    )

    # build summary
    column_b = ytd_transactions.aggregate(
        line_11ai=get_line("SA11AI"),
        line_11aii=get_line("SA11AII"),
        line_11b=get_line("SA11B"),
        line_11c=get_line("SA11C"),
        line_12=get_line("SA12"),
        line_13=get_line("SA13"),
        line_14=get_line("SA14"),
        line_15=get_line("SA15"),
        line_16=get_line("SA16"),
        line_17=get_line("SA17"),
        line_21b=get_line("SB21B"),
        line_22=get_line("SB22"),
        line_23=get_line("SB23"),
        line_24=get_line("SE"),
        line_25=get_line("SF"),
        line_26=get_line("SB26"),
        line_27=get_line("SB27"),
        line_28a=get_line("SB28A"),
        line_28b=get_line("SB28B"),
        line_28c=get_line("SB28C"),
        line_29=get_line("SB29"),
        line_30b=get_line("SB30B"),
    )

    column_b["line_11aiii"] = column_b["line_11ai"] + column_b["line_11aii"]
    column_b["line_11d"] = (
        column_b["line_11aiii"] + column_b["line_11b"] + column_b["line_11c"]
    )
    column_b["line_18c"] = Decimal(0)  # Stubbed out until a future ticket
    column_b["line_21ai"] = Decimal(0)  # Stubbed out until a future ticket
    column_b["line_21aii"] = Decimal(0)  # Stubbed out until a future ticket
    column_b["line_21c"] = (
        column_b["line_21ai"] + column_b["line_21aii"] + column_b["line_21b"]
    )
    column_b["line_28d"] = (
        column_b["line_28a"] + column_b["line_28b"] + column_b["line_28c"]
    )
    column_b["line_30ai"] = Decimal(0)  # Stubbed out until a future ticket
    column_b["line_30aii"] = Decimal(0)  # Stubbed out until a future ticket
    column_b["line_30c"] = (
        column_b["line_30ai"] + column_b["line_30aii"] + column_b["line_30b"]
    )
    column_b["line_31"] = (
        column_b["line_21c"]
        + column_b["line_22"]
        + column_b["line_23"]
        + column_b["line_24"]
        + column_b["line_25"]
        + column_b["line_26"]
        + column_b["line_27"]
        + column_b["line_28d"]
        + column_b["line_29"]
        + column_b["line_30c"]
    )
    column_b["line_32"] = (
        column_b["line_31"] - column_b["line_21aii"] - column_b["line_30aii"]
    )
    column_b["line_33"] = column_b["line_11d"]
    column_b["line_34"] = column_b["line_28d"]
    column_b["line_35"] = column_b["line_33"] - column_b["line_34"]
    column_b["line_36"] = column_b["line_21ai"] + column_b["line_21b"]
    column_b["line_37"] = column_b["line_15"]
    column_b["line_38"] = column_b["line_36"] - column_b["line_37"]
    column_b["line_6c"] = (
        column_b["line_11d"]
        + column_b["line_12"]
        + column_b["line_13"]
        + column_b["line_14"]
        + column_b["line_15"]
        + column_b["line_16"]
        + column_b["line_17"]
        + column_b["line_18c"]
    )
    column_b["line_7"] = column_b["line_31"]
    column_b["line_19"] = column_b["line_6c"]
    column_b["line_20"] = column_b["line_19"] - column_b["line_18c"]

    return column_b


def calculate_cash_on_hand_fields(report, column_a, column_b):

    reports_from_prior_years = Report.objects.filter(
        Q(form_3x__isnull=False),
        committee_account=report.committee_account,
        coverage_through_date__year__lt=report.coverage_from_date.year,
    ).order_by("coverage_from_date")
    closest_report_from_prior_years = reports_from_prior_years.last()
    year_of_closest_report = (
        closest_report_from_prior_years.coverage_from_date.year
        if closest_report_from_prior_years
        else 0
    )

    """ Get the most recent cash on hand override that is
        for a year after the closest report from prior years """
    cash_on_hand_override = (
        CashOnHandYearly.objects.filter(
            committee_account=report.committee_account,
            year__lte=report.coverage_from_date.year,
            year__gt=year_of_closest_report,
        )
        .order_by("-year")
        .first()
    )

    cash_on_hand_override = (
        cash_on_hand_override.cash_on_hand if cash_on_hand_override else None
    )

    previous_report_this_year = (
        Report.objects.filter(
            ~Q(id=report.id),
            Q(form_3x__isnull=False),
            committee_account=report.committee_account,
            coverage_through_date__year=report.coverage_from_date.year,
            coverage_through_date__lt=report.coverage_from_date,
        )
        .order_by("-coverage_through_date")
        .first()
    )
    if cash_on_hand_override is not None:
        column_b["line_6a"] = cash_on_hand_override
    elif (
        closest_report_from_prior_years is not None
        and closest_report_from_prior_years.form_3x is not None
    ):
        column_b["line_6a"] = (
            closest_report_from_prior_years.form_3x.L8_cash_on_hand_close_ytd
        )  # noqa: E501
    else:
        # user defined cash on hand
        column_b["line_6a"] = 0

    if (
        previous_report_this_year is not None
        and previous_report_this_year.form_3x is not None
    ):
        column_a["line_6b"] = (
            previous_report_this_year.form_3x.L8_cash_on_hand_at_close_period
        )  # noqa: E501
    else:
        # user defined cash on hand
        column_a["line_6b"] = column_b["line_6a"]

    # if we have cash on hand values
    if column_a.get("line_6b") is not None and column_b.get("line_6a") is not None:
        column_a["line_6d"] = column_a["line_6b"] + column_a["line_6c"]
        column_a["line_8"] = column_a["line_6d"] - column_a["line_7"]
        column_b["line_6d"] = column_b["line_6a"] + column_b["line_6c"]
        column_b["line_8"] = column_b["line_6d"] - column_b["line_7"]
    return column_a, column_b


def get_line(form_type, field="amount"):
    query = Q(~Q(memo_code=True), form_type=form_type)
    return Coalesce(Sum(field, filter=query), Decimal(0.0))

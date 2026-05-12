from fecfiler.reports.models import Report
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.models import Contact
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.user.models import User
from statistics import quantiles, mean
import structlog

logger = structlog.get_logger(__name__)


def get_averages(items):
    length = len(items)
    if not items or length == 0:
        raise ValueError("Cannot get averages for an empty list")

    data = sorted(items)
    avg = mean(data)

    if length < 4:
        return {"Mean": avg}

    q1, q2, q3 = quantiles(data)

    return {
        "1st quartile": q1,
        "2nd quartile": q2,
        "3rd quartile": q3,
        "Max": data[-1],
        "Mean": avg,
    }


def print_keyvalues(dict):
    for key in dict.keys():
        # when outputting, label the 2nd quartile as median
        suffix = " (median)" if key == "2nd quartile" else ""

        # limit floats to 3 decimal places and strip trailing zeros
        value = dict[key]
        value_str = (
            f"{value:.3f}".rstrip("0").rstrip(".")
            if isinstance(value, float)
            else str(value)
        )

        logger.info(f"{f'   {key}: {value_str}{suffix}':<60}")


def get_num_committees():
    logger.info(f"{f'Number of committees: {CommitteeAccount.objects.count()}':<60}")


def get_num_users():
    logger.info(f"{f'Number of users: {User.objects.count()}':<60}")


def get_num_reports():
    logger.info(f"{f'Number of reports: {Report.objects.count()}':<60}")


def get_num_reports_per_committee(committee_id=None):
    if committee_id:
        report_count = Report.objects.filter(
            committee_account__committee_id=committee_id
        ).count()
        logger.info(
            f"{(
                f'Number of reports for committee {committee_id}: '
                + f'{report_count}'
            ):<60}"
        )
    else:
        committee_report_counts = []
        for committee in CommitteeAccount.objects.all():
            r_count = Report.objects.filter(committee_account=committee).count()
            committee_report_counts.append(r_count)

        if not committee_report_counts:
            logger.info(f"{'Number of reports per committee: no committees':<60}")
            return

        averages = get_averages(committee_report_counts)

        logger.info(f"{f'Number of reports per committee:':<60}")
        print_keyvalues(averages)


def get_num_transactions_per_committee(committee_id=None):
    if committee_id:
        transaction_count = Transaction.objects.filter(
            committee_account__committee_id=committee_id
        ).count()
        logger.info(
            f"{(
                f'Number of transactions for committee {committee_id}: '
                + f'{transaction_count}'
            ):<60}"
        )
    else:
        committee_transaction_counts = []
        highest_count = -1
        biggest_committee = None
        for committee in CommitteeAccount.objects.all():
            t_count = Transaction.objects.filter(committee_account=committee).count()
            committee_transaction_counts.append(t_count)
            if t_count > highest_count:
                highest_count = t_count
                biggest_committee = committee

        if not committee_transaction_counts:
            logger.info(f"{'Number of transactions per committee: no committees':<60}")
            return

        averages = get_averages(committee_transaction_counts)

        logger.info(f"{f'Number of transactions per committee:':<60}")
        print_keyvalues(averages)
        logger.info(
            f"{(
                '   The largest committee is '
                + f'{biggest_committee.committee_id} with {highest_count} transactions'
            ):<60}"
        )


def get_num_transactions_per_report(committee_id=None):
    report_transaction_counts = []
    for report in Report.objects.all():
        if committee_id and report.committee_account.committee_id != committee_id:
            continue
        t_count = Transaction.objects.filter(reports=report).count()
        report_transaction_counts.append(t_count)

    if not report_transaction_counts:
        logger.info(
            f"{(
                'Number of transactions per report'
                + (
                    f' for committee_id {committee_id}'
                    if committee_id is not None
                    else ''
                )
                + ': no reports'
            ):<60}"
        )
        return

    averages = get_averages(report_transaction_counts)

    logger.info(
        f"{(
            'Number of transactions per report'
            + (f' for committee_id {committee_id}:' if committee_id is not None else ':')
        ):<60}"
    )
    print_keyvalues(averages)


def get_num_transactions_per_contact():
    contact_transaction_counts = []
    for c in Contact.objects.all():
        ct_set_keys = []
        for i in range(1, 6):
            ct_set_keys.append(f"contact_{i}_transaction_set")

        for n in ["I", "II", "III", "IV", "V"]:
            ct_set_keys.append(f"contact_candidate_{n}_transaction_set")

        ct_set_keys.append("contact_affiliated_transaction_set")
        transaction_count = 0
        for key in ct_set_keys:
            transaction_count += getattr(c, key).count()

        contact_transaction_counts.append(transaction_count)

    if not contact_transaction_counts:
        logger.info(f"{'Number of transactions per contact: no contacts':<60}")
        return

    averages = get_averages(contact_transaction_counts)

    logger.info(f"{f'Number of transactions per contact:':<60}")
    print_keyvalues(averages)


def get_transaction_types_breakdown():
    tti_counts = {}
    for transaction in Transaction.objects.all():
        tti = transaction.transaction_type_identifier
        tti_counts[tti] = tti_counts.get(tti, 0) + 1

    logger.info(f"{f'Transaction types breakdown:':<60}")
    print_keyvalues(tti_counts)


def get_transaction_tiers_breakdown():
    filter_keys = [
        {"parent_transaction__isnull": True},
        {
            "parent_transaction__isnull": False,
            "parent_transaction__parent_transaction__isnull": True,
        },
        {"parent_transaction__parent_transaction__isnull": False},
    ]
    logger.info(f"{f'Transaction tiers breakdown:':<60}")
    for i in range(3):
        tier = "I" * (i + 1)
        count = Transaction.objects.filter(**filter_keys[i]).count()
        logger.info(f"{f'   Tier {tier}: {count}':<60}")


def get_carryover_type_transactions():
    logger.info(f"{f'Carryover transactions:':<60}")
    for model in [ScheduleC, ScheduleC2, ScheduleD]:
        logger.info(f"{f'   {model.__name__}: {model.objects.count()}':<60}")

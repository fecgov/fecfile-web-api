from fecfiler.reports.models import Report
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.models import Contact
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_d.models import ScheduleD
from django.contrib.auth import get_user_model
import structlog

logger = structlog.get_logger(__name__)


def get_averages(items):
    length = len(items)
    if length == 0:
        raise ValueError("Cannot get averages for an empty list")

    mean = sum(items) / length
    if len(items) < 4:
        return {"Mean": mean}

    items.sort()
    first_q = items[:length // 4]
    second_q = items[length // 4:length // 2]
    third_q = items[length // 2:length // 4 * 3]
    fourth_q = items[length // 4 * 3:]
    return {
        "1st quartile": first_q[-1],
        "2nd quartile": second_q[-1],
        "3rd quartile": third_q[-1],
        "Max": fourth_q[-1],
        "Mean": mean,
    }


def print_keyvalues(dict):
    for key in dict.keys():
        logger.info(f"{key}: {dict[key]}")


def get_num_committees():
    logger.info(f"Number of committees: {CommitteeAccount.objects.count()}")


def get_num_users():
    User = get_user_model()
    logger.info(f"Number of users: {User.objects.count()}")


def get_num_reports():
    logger.info(f"Number of reports: {Report.objects.count()}")


def get_num_reports_per_committee(committee_id=None):
    if committee_id:
        report_count = Report.objects.filter(
            committee_account__committee_id=committee_id
        ).count()
        logger.info(f"Number of reports for committee {committee_id}: {report_count}")
    else:
        committee_report_counts = []
        for committee in CommitteeAccount.objects.all():
            r_count = Report.objects.filter(committee_account=committee).count()
            committee_report_counts.append(r_count)

        averages = get_averages(committee_report_counts)

        logger.info(
            "\nNumber of reports per committee:"
            "\n--------------------------------"
        )
        print_keyvalues(averages)


def get_num_transactions_per_committee(committee_id=None):
    if committee_id:
        transaction_count = Transaction.objects.filter(
            committee_account__committee_id=committee_id
        ).count()
        logger.info(f"Number of transactions for committee {committee_id}: {transaction_count}")
    else:
        committee_transaction_counts = []
        highest_count = 0
        biggest_committee = None
        for committee in CommitteeAccount.objects.all():
            t_count = Transaction.objects.filter(committee_account=committee).count()
            committee_transaction_counts.append(t_count)
            if t_count > highest_count:
                highest_count = t_count
                biggest_committee = committee

        averages = get_averages(committee_transaction_counts)

        logger.info(
            "\nNumber of transactions per committee:"
            "\n-------------------------------------"
        )
        print_keyvalues(averages)
        logger.info(
            "The largest committee is"
            f" {biggest_committee.committee_id} with {highest_count} transactions"
        )


def get_num_transactions_per_report(committee_id=None):
    report_transaction_counts = []
    for report in Report.objects.all():
        if committee_id and report.committee_account.committee_id != committee_id:
            continue
        t_count = Transaction.objects.filter(reports=report).count()
        report_transaction_counts.append(t_count)

    averages = get_averages(report_transaction_counts)

    logger.info(
        "\nNumber of transactions per report:"
        "\n----------------------------------"
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

    averages = get_averages(contact_transaction_counts)

    logger.info("\nNumber of transactions per contact:\n-----------------------------------")
    print_keyvalues(averages)


def get_transaction_types_breakdown():
    tti_counts = {}
    for transaction in Transaction.objects.all():
        tti = transaction.transaction_type_identifier
        tti_counts[tti] = tti_counts.get(tti, 0) + 1

    logger.info("\nTransaction types breakdown:\n----------------------------")
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
    logger.info("\nTransaction tiers breakdown:\n----------------------------")
    for i in range(3):
        logger.info(
            f"Tier {'I' * (i + 1)}: "
            f"{Transaction.objects.filter(**filter_keys[i]).count()}"
        )


def get_carryover_type_transactions():
    logger.info("\nCarryover transactions:\n-----------------------")
    for model in [ScheduleC, ScheduleC2, ScheduleD]:
        logger.info(f"{model.__name__}: {model.objects.count()}")

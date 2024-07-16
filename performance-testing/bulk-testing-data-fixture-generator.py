import json
from random import choice, choices, randrange
import string
import os
from uuid import UUID, uuid4


PRIMARY_COMMITTEE_FEC_ID = os.environ.get("LOCAL_TEST_USER", "C00000000")
PRIMARY_COMMITTEE_UUID = os.environ.get("LOCAL_TEST_COMMITTEE_UUID", uuid4())
CONTACT_TYPES = ["IND", "ORG", "COM", "CAN"]
SCHEDULE_FORMATS = {
    "A": {
        "schedule_name": "schedulea",
        "amount_prefix": "contribution",
        "date_prefix": "contribution",
        "schedule_id_field": "schedule_a_id",
    },
    "B": {
        "schedule_name": "scheduleb",
        "amount_prefix": "expenditure",
        "date_prefix": "expenditure",
        "schedule_id_field": "schedule_b_id",
    },
    "C": {
        "schedule_name": "schedulec",
        "amount_prefix": "loan",
        "date_prefix": "loan_incurred",
        "schedule_id_field": "schedule_c_id",
    },
    # Including Schedule D transactions was blocking Django from
    # importing the resulting fixture cleanly.
    # "D": {
    #     "schedule_name": "scheduled",
    #     "amount_prefix": "incurred",
    #     "date_prefix": None,
    #     "schedule_id_field": "schedule_d_id",
    # },
    "E": {
        "schedule_name": "schedulee",
        "amount_prefix": "expenditure",
        "date_prefix": "disbursement",
        "schedule_id_field": "schedule_e_id",
    },
}
F3X_DATE_DATA = [
    {
        "report_code": "M2",
        "year": 2000,
        "from_date": "01-01",
        "through_date": "01-31"
    },
    {
        "report_code": "M3",
        "year": 2000,
        "from_date": "02-01",
        "through_date": "02-28"
    },
    {
        "report_code": "M4",
        "year": 2000,
        "from_date": "03-01",
        "through_date": "03-31"
    },
    {
        "report_code": "M5",
        "year": 2000,
        "from_date": "04-01",
        "through_date": "04-30"
    },
    {
        "report_code": "M6",
        "year": 2000,
        "from_date": "05-01",
        "through_date": "05-31"
    },
    {
        "report_code": "M7",
        "year": 2000,
        "from_date": "06-01",
        "through_date": "06-30"
    },
    {
        "report_code": "M8",
        "year": 2000,
        "from_date": "07-01",
        "through_date": "07-31"
    },
    {
        "report_code": "M9",
        "year": 2000,
        "from_date": "08-01",
        "through_date": "08-31"
    },
    {
        "report_code": "M10",
        "year": 2000,
        "from_date": "09-01",
        "through_date": "09-30"
    },
    {
        "report_code": "M11",
        "year": 2000,
        "from_date": "10-01",
        "through_date": "10-31"
    },
    {
        "report_code": "M12",
        "year": 2000,
        "from_date": "11-01",
        "through_date": "11-30"
    },
    {
        "report_code": "YE",
        "year": 2000,
        "from_date": "12-01",
        "through_date": "12-31"
    },
]


def random_string(length, use_letters=True, use_digits=False, use_punctuation=False):
    character_pool = ""
    if use_letters:
        character_pool += string.ascii_letters
    if use_digits:
        character_pool += string.digits
    if use_punctuation:
        character_pool += "!.?$@,#+=%&"

    if len(character_pool) == 0:
        return ""

    return "".join(choices(character_pool, k=length))


def get_record_uuid(record):
    return record["fields"]["id"]


def get_committee(committee_fec_id, committee_uuid):
    return {
        "model": "committee_accounts.CommitteeAccount",
        "fields": {
            "id": committee_uuid,
            "committee_id": committee_fec_id,
            "created": "2024-01-01T00:00:00.000Z",
            "updated": "2024-01-01T00:00:00.000Z"
        }
    }


def create_committee(committee_fec_id=None, committee_uuid=None):
    if committee_fec_id is None:
        committee_fec_id = f"C{random_string(8, use_letters=False, use_digits=True)}"
    if committee_uuid is None:
        committee_uuid = uuid4()

    return get_committee(committee_fec_id, committee_uuid)


def get_form_3x_date_data():
    data = F3X_DATE_DATA.pop(0)
    out_data = {
        "report_code": data["report_code"],
        "coverage_from_date": f"{data['year']}-{data['from_date']}",
        "coverage_through_date": f"{data['year']}-{data['through_date']}",
        "date_signed": f"{data['year']}-{data['through_date']}"
    }
    data["year"] += 1
    F3X_DATE_DATA.append(data)
    return out_data


def get_form_3x(form_3x_id):
    return {
        "model": "reports.Form3X",
        "fields": {
            "id": form_3x_id,
            "change_of_address": False,
            "qualified_committee": False,
        }
    }


def get_report(report_id, form_3x_id, committee_uuid):
    return {
        "model": "reports.report",
        "fields": {
            "id": report_id,
            "form_3x_id": form_3x_id,
            "committee_account_id": committee_uuid,
            "form_type": "F3XN",
            "calculation_status": None,
            "treasurer_last_name": random_string(8),
            "treasurer_first_name": random_string(8),
            "treasurer_middle_name": random_string(5),
            "treasurer_prefix": random_string(3, use_punctuation=True),
            "treasurer_suffix": random_string(3, use_punctuation=True),
            "created": "2024-01-01T00:00:00.000Z",
            "updated": "2024-01-01T00:00:00.000Z"
        } | get_form_3x_date_data()
    }


def create_report(committee_uuid, report_id=None, form_3x_id=None):
    if report_id is None:
        report_id = uuid4()
    if form_3x_id is None:
        form_3x_id = uuid4()

    return [
        get_form_3x(form_3x_id),
        get_report(report_id, form_3x_id, committee_uuid)
    ]


def get_contact(contact_id, committee_uuid, contact_type):
    contact = {
        "model": "contacts.contact",
        "fields": {
            "id": contact_id,
            "type": contact_type,
            "committee_account_id": committee_uuid,
            "street_1": random_string(16, use_digits=True),
            "street_2": random_string(6, use_digits=True),
            "city": random_string(10),
            "state": random_string(2),
            "zip": random_string(2, use_letters=False, use_digits=True),
            "country": "USA",
            "created": "2024-01-01T00:00:00.000Z",
            "updated": "2024-01-01T00:00:00.000Z"
        }
    }

    if contact_type in ["COM", "ORG"]:
        contact["fields"] |= {
            "name": random_string(16, use_digits=True, use_punctuation=True)
        }
        if contact_type == "COM":
            contact["fields"] |= {
                "committee_id": f"C{random_string(8, use_letters=False, use_digits=True)}"
            }
    if contact_type in ["IND", "CAN"]:
        contact["fields"] |= {
            "telephone": random_string(10, use_letters=False, use_digits=True),
            "last_name": random_string(8),
            "first_name": random_string(8),
            "middle_name": random_string(5),
            "prefix": random_string(3, use_punctuation=True),
            "suffix": random_string(3, use_punctuation=True),
            "employer": random_string(16, use_digits=True, use_punctuation=True),
            "occupation": random_string(12, use_digits=True, use_punctuation=True),
        }
        if contact_type == "CAN":
            candidate_office = choice(["H", "S", "P"])
            candidate_district = random_string(1, use_letters=False, use_digits=True)
            candidate_state = random_string(2)
            candidate_id = f"""{candidate_office}{candidate_district}{candidate_state}{
                random_string(5, use_letters=False, use_digits=True)
            }"""
            contact["fields"] |= {
                "candidate_state": candidate_state,
                "candidate_office": candidate_office,
                "candidate_district": candidate_district,
                "candidate_id": candidate_id
            }

    return contact


def create_contact(committee_uuid, contact_id=None):
    if contact_id is None:
        contact_id = uuid4()

    contact_format = choice(CONTACT_TYPES)
    return get_contact(contact_id, committee_uuid, contact_format)


def get_sched_transaction(sched_transaction_id, amount, date, schedule_format):
    amount_prefix = schedule_format["amount_prefix"]
    date_prefix = schedule_format["date_prefix"]

    return {
        "model": f"transactions.{schedule_format['schedule_name']}",
        "fields": {
            "id": f"{sched_transaction_id}",
            f"{amount_prefix}_amount": amount,
        } | {f"{date_prefix}_date": f"{date}"} if date_prefix else {}
    }


def get_transaction(
    transaction_id, sched_transaction_id, committee_uuid, contact_id, schedule
):
    return {
        "model": "transactions.transaction",
        "fields": {
            "id": f"{transaction_id}",
            f"{schedule['schedule_id_field']}": f"{sched_transaction_id}",
            "committee_account_id": f"{committee_uuid}",
            "_form_type": "SA11AI",
            "memo_code": choices([True, False], [0.8, 0.2], k=1)[0],
            "contact_1_id": f"{contact_id}",
            "aggregation_group": "GENERAL",
            "transaction_type_identifier": "INDIVIDUAL_RECEIPT",
            "aggregate": 0,
            "_calendar_ytd_per_election_office": None,
            "loan_payment_to_date": None,
            "created": "2024-01-01T00:00:00.000Z",
            "updated": "2024-01-01T00:00:00.000Z"
        }
    }


def get_transaction_report(transaction_id, report_id):
    return {
        "model": "reports.reporttransaction",
        "fields": {
            "transaction_id": f"{transaction_id}",
            "report_id": f"{report_id}",
            "created": "2024-01-01T00:00:00.000Z",
            "updated": "2024-01-01T00:00:00.000Z"
        }
    }


def create_transaction(committee_uuid, contact_id, report):
    schedule = choice(list(SCHEDULE_FORMATS.values()))
    report_id = get_record_uuid(report)
    report_date = report["fields"]["coverage_from_date"]

    sched_transaction_id = uuid4()
    transaction_id = uuid4()
    return [
        get_sched_transaction(
            sched_transaction_id, randrange(100, 500), report_date, schedule
        ),
        get_transaction(
            transaction_id, sched_transaction_id, committee_uuid, contact_id, schedule
        ),
        get_transaction_report(transaction_id, report_id)
    ]


def create_records(transaction_count, report_count, contact_count, committee_count):
    committees = [create_committee(PRIMARY_COMMITTEE_FEC_ID, PRIMARY_COMMITTEE_UUID)]
    for _ in range(max(committee_count, 0)):
        committees.append(create_committee())

    committee_records = {}
    for comm in committees:
        committee_uuid = get_record_uuid(comm)
        committee_records[committee_uuid] = {
            "committee_record": comm,
            "form_3xs": [],
            "reports": [],
            "contacts": [],
            "sched_transactions": [],
            "transactions": [],
            "transaction_reports": []
        }
        committee_record = committee_records[committee_uuid]

        for _ in range(max(report_count, 1)):
            form_3x, report = create_report(committee_uuid)
            committee_record["form_3xs"].append(form_3x)
            committee_record["reports"].append(report)

        for _ in range(max(contact_count, 1)):
            contact = create_contact(committee_uuid)
            committee_record["contacts"].append(contact)

        for _ in range(max(transaction_count, 1)):
            report = choice(committee_record["reports"])
            contact = choice(committee_record["contacts"])
            contact_id = get_record_uuid(contact)
            sched, trans, trans_rep = create_transaction(
                committee_uuid, contact_id, report
            )
            committee_record["sched_transactions"].append(sched)
            committee_record["transactions"].append(trans)
            committee_record["transaction_reports"].append(trans_rep)

    return committee_records


def prepare_records(records):
    out_records = []
    for c in records.values():
        if c["committee_record"]["fields"]["committee_id"] != PRIMARY_COMMITTEE_FEC_ID:
            out_records.append(c["committee_record"])

    for c in records.values():
        out_records += (
            c["form_3xs"]
            + c["reports"]
            + c["contacts"]
            + c["sched_transactions"]
            + c["transactions"]
            + c["transaction_reports"]
        )
    return out_records


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return obj.hex
        return json.JSONEncoder.default(self, obj)


def save_records_to_fixture(records):
    directory = os.getcwd()
    filename = "bulk-testing-data.locust.json"
    full_filename = os.path.join(directory, filename)
    file = open(full_filename, "w")
    file.write(json.dumps(records, cls=UUIDEncoder))
    file.close()


def create_fixture(transactions=1000, reports=5, contacts=100, committees=1):
    records = create_records(transactions, reports, contacts, committees)
    sorted_records = prepare_records(records)
    save_records_to_fixture(sorted_records)

    return sorted_records


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="""This script generates json test data for
            use in performance testing."""
    )
    """
        Creating committees with a fixture leads to a transaction_view related error when
        loading the fixture into the database.
    """
    # parser.add_argument(
    #     "--committees",
    #     default=0,
    #     type=int,
    #     help="""The number of committees in addition to the testing committee
    #         to be created. Defaults to zero (0)."""
    # )
    parser.add_argument(
        "--reports",
        default=5,
        type=int,
        help="""The number of form-3x reports to be created in each committee.
            Reports are comprised of two records each. Defaults to five (5).""",
    )
    parser.add_argument(
        "--contacts",
        default=100,
        type=int,
        help="""The number of contacts to be created in each committee.
            Defaults to one hundred (100)."""
    )
    parser.add_argument(
        "--transactions",
        default=1000,
        type=int,
        help="""The number of transactions to be created in each committee.
            Transactions are comprised of three records each.
            Defaults to one thousand (1,000)."""
    )
    args = parser.parse_args()

    sorted_records = create_fixture(
        args.transactions,
        args.reports,
        args.contacts,
        committees=0  # args.committees
    )
    print(f"Generated fixture with {'{:,}'.format(len(sorted_records))} records")

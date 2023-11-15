import argparse
from random import randrange, choice

# Generate Transaction Record Fixture
#
#    Creates a json file containing valid transaction records
#    for the form_type values specified by the user, and with
#    randomly generated values for transaction_amount.

def get_arguments():
    parser = argparse.ArgumentParser(
        prog='Generate  Transaction Record Fixture',
        description='Creates a json file containing valid transaction records\n' +
                    'for the form_type values specified by the user, and with\n' +
                    'randomly generated values for transaction_amount.'
    )

    parser.add_argument(
        'form_types',
        nargs='+',
        default=[],
        help="form_type values (e.g SA12 or SC/9) separated by spaces"
    )
    parser.add_argument(
        '--committee_account_id',
        default="735db943-9446-462a-9be0-c820baadb622",
        help='default value: 735db943-9446-462a-9be0-c820baadb622'
    )
    parser.add_argument(
        '--report_id',
        default="b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
        help='default value: b6d60d2d-d926-4e89-ad4b-c47d152a66ae'
    )
    parser.add_argument(
        '--report_start_date',
        default="2005-01-30",
        help='default value: 2005-01-30'
    )
    parser.add_argument(
        '--report_end_date',
        default="2005-02-28",
        help='default value: 2005-02-28'
    )
    parser.add_argument(
        '--output_file',
        help="Output to a file instead of the console (e.g --output_file=records.txt)")

    return parser.parse_args()

def get_schedule(form_type):
    schedule =  str(form_type[1]).capitalize()  # the second char in the form_type
    if schedule == "C":
        if form_type[2] in ["1", "2"]:
            schedule = form_type[1:2]
    return schedule

def get_date(args, test_case):
    report_start = args.report_start_date.split("-")
    report_end = args.report_end_date.split("-")

    if "within_dates" in test_case:
        return "-".join(report_start)
    if "year" in test_case:
        report_months = range(int(report_start[1]), int(report_end[1])+1)
        year = report_start[0]
        months = [str(m).rjust(2, "0") for m in range(1,13)]
        random_month = choice(list(set(months) - set(report_months)))
        return f"{year}-{random_month}-01"

    report_years = set([report_start[0], report_end[0]])
    random_year = choice(list(set(range(2000-50, 2000+50)) - report_years))
    random_month = choice([str(m).rjust(2, "0") for m in range(1,13)])
    return f"{random_year}-{random_month}-01"

def random_hex(length=1):
    hex_chars = "0123456789abcdef"

    out_string = ""
    while len(out_string) < length:
        out_string += choice(hex_chars)

    return out_string

def get_id(form_type, record_number, schedule=""):
    hex_chars = "0123456789abcdef"

    schedule_str = ""
    if(schedule[0].lower() in hex_chars):
        schedule_str += schedule.lower()
    else:
        schedule_str += hex(ord(schedule.lower()))[2:]

    line_number = form_type.split(schedule)[1].strip('/')
    schedule_str+="0"+str(line_number)
    schedule_str = schedule_str.ljust(8, "0")

    record_str = str(record_number).rjust(12, "0")

    return f"{schedule_str}-{random_hex(4)}-{random_hex(4)}-{random_hex(4)}-{record_str}"

def get_records(form_type, args):
    records = []
    test_cases = [
        "within_dates",
        "within_dates",
        "within_year",
        "outside_dates",
        "within_dates_but_memo"
    ]
    for record_number in range(len(test_cases)):
        test_case = test_cases[record_number]
        comment = "Comment"
        if test_case == "within_dates":
            comment = f"{form_type} within report dates, should count in Col. A"
        if test_case == "within_year":
            comment = f"{form_type} within year, should count in Col. B"
        if test_case == "outside_dates":
            comment = f"{form_type} outside of dates, should not count"
        if test_case == "within_dates_but_memo":
            comment = f"{form_type} is a memo item, should not count"

        schedule = get_schedule(form_type)

        schedule_id = get_id(form_type, record_number, schedule)
        transaction_id = get_id(form_type, record_number, schedule)

        schedule_model = f"schedule{schedule.lower()}"

        amount_field = "amount"
        if schedule == "A":
            amount_field = "contribution_amount"
        if schedule == "B":
            amount_field = "expenditure_amount"
        if schedule == "C":
            amount_field = "loan_amount"
        if schedule == "C1":
            amount_field = "loan_amount"
        if schedule == "C2":
            amount_field = "guaranteed_amount"
        if schedule == "D":
            amount_field = "incurred_amount"
        if schedule == "E":
            amount_field = "expenditure_amount"

        amount = randrange(20, 150)

        date_field = ""
        if schedule == "A":
            date_field = "contribution_date"
        if schedule == "B":
            date_field = "expenditure_date"
        if schedule == "C":
            date_field = "loan_incurred_date"
        if schedule == "C1":
            date_field = "loan_incurred_date"
        if schedule == "C2":
            date_field = ""
        if schedule == "D":
            date_field = ""
        if schedule == "E":
            date_field = "disbursement_date"

        date = get_date(args, test_case)

        print(schedule, date_field)
        date_entry = ""
        if (len(date_field) > 0):
            date_entry = f''',\n{" "*12}"{date_field}": "{date}"'''

        memo_code = (test_case=="within_dates_but_memo")

        schedule_record = f"""    {{
        "comment": "{comment}",
        "model": "transactions.{schedule_model}",
        "fields": {{
            "id": "{schedule_id}",
            "{amount_field}": {amount}{date_entry}
        }}\n    }}"""

        transaction_record = f"""    {{
        "comment": "{comment}",
        "model": "transactions.transaction",
        "fields": {{
            "id": "{transaction_id}",
            "schedule_{schedule.lower()}_id": "{schedule_id}",
            "committee_account_id": "{args.committee_account_id}",
            "report_id": "{args.report_id}",
            "_form_type": "{form_type}",
            "memo_code": {str(memo_code).lower()},
            "created": "2022-02-09T00:00:00.000Z",
            "updated": "2022-02-09T00:00:00.000Z",
            "transaction_type_identifier": "Transaction Type Identifier"
        }}\n    }}"""

        records.append(schedule_record)
        records.append(transaction_record)

    return records



if (__name__ == "__main__"):
    args = get_arguments()

    records = []
    for form_type in args.form_types:
        records += get_records(form_type, args)

    records_str = ",\n".join(records)
    output = "[\n" + records_str + "\n]"

    if not args.output_file:
        print(output)
    else:
        file = open(args.output_file, 'w')
        file.write(output)
        file.close()





"""
    {
        "comment": "SA17 transaction before report dates; should count in Column B",
        "model": "transactions.schedulea",
        "fields": {
            "id": "a11aefe8-9b5f-4539-b7e5-170000000008",
            "contribution_amount": 100,
            "contribution_date": "2005-01-01"
        }
    },
    {
        "comment": "SA17 transaction before report dates; should count in Column B",
        "model": "transactions.transaction",
        "fields": {
            "id": "a12aefe8-9b5f-4539-b7e5-170000000008",
            "schedule_a_id": "a11aefe8-9b5f-4539-b7e5-170000000008",
            "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
            "report_id": "1406535e-f99f-42c4-97a8-247904b7d297",
            "_form_type": "SA17",
            "memo_code": false,
            "created": "2022-02-09T00:00:00.000Z",
            "updated": "2022-02-09T00:00:00.000Z",
            "transaction_type_identifier": "INDIVIDUAL_RECEIPT"
        }
    },
    {
        "comment": "SA17 transaction to count",
        "model": "transactions.schedulea",
        "fields": {
            "id": "a11aefe8-9b5f-4539-b7e5-170000000002",
            "contribution_amount": 200.50,
            "contribution_date": "2005-02-01"
        }
    },
    {
        "comment": "SA17 transaction to count with SA17",
        "model": "transactions.transaction",
        "fields": {
            "id": "a12aefe8-9b5f-4539-b7e5-170000000002",
            "schedule_a_id": "a11aefe8-9b5f-4539-b7e5-170000000002",
            "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "_form_type": "SA17",
            "memo_code": false,
            "created": "2022-02-09T00:00:00.000Z",
            "updated": "2022-02-09T00:00:00.000Z",
            "transaction_type_identifier": "INDIVIDUAL_RECEIPT"
        }
    },
    {
        "comment": "SA17 transaction to count",
        "model": "transactions.schedulea",
        "fields": {
            "id": "a11aefe8-9b5f-4539-b7e5-170000000003",
            "contribution_amount": -1,
            "contribution_date": "2005-02-01"
        }
    },
    {
        "comment": "SA17 transaction to count with SA17",
        "model": "transactions.transaction",
        "fields": {
            "id": "a12aefe8-9b5f-4539-b7e5-170000000003",
            "schedule_a_id": "a11aefe8-9b5f-4539-b7e5-170000000003",
            "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "_form_type": "SA17",
            "memo_code": false,
            "created": "2022-02-09T00:00:00.000Z",
            "updated": "2022-02-09T00:00:00.000Z",
            "transaction_type_identifier": "INDIVIDUAL_RECEIPT"
        }
    },
    {
        "comment": "SA17 transaction to not count",
        "model": "transactions.schedulea",
        "fields": {
            "id": "a11aefe8-9b5f-4539-b7e5-170000000004",
            "contribution_amount": 500,
            "contribution_date": "2005-02-01"
        }
    },
    {
        "comment": "SA17 transaction to not count with SA17",
        "model": "transactions.transaction",
        "fields": {
            "id": "a12aefe8-9b5f-4539-b7e5-170000000004",
            "schedule_a_id": "a11aefe8-9b5f-4539-b7e5-170000000004",
            "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
            "report_id": "1406535e-f99f-42c4-97a8-247904b7d297",
            "_form_type": "SA17",
            "memo_code": true,
            "created": "2022-02-09T00:00:00.000Z",
            "updated": "2022-02-09T00:00:00.000Z",
            "transaction_type_identifier": "INDIVIDUAL_RECEIPT"
        }
    },
    {
        "comment": "SA17 transaction to count",
        "model": "transactions.schedulea",
        "fields": {
            "id": "a11aefe8-9b5f-4539-b7e5-170000000001",
            "contribution_amount": 800.50,
            "contribution_date": "2005-02-01"
        }
    },
    {
        "comment": "SA17 transaction to count with SA17",
        "model": "transactions.transaction",
        "fields": {
            "id": "a12aefe8-9b5f-4539-b7e5-170000000001",
            "schedule_a_id": "a11aefe8-9b5f-4539-b7e5-170000000001",
            "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "_form_type": "SA17",
            "memo_code": false,
            "created": "2022-02-09T00:00:00.000Z",
            "updated": "2022-02-09T00:00:00.000Z",
            "transaction_type_identifier": "INDIVIDUAL_RECEIPT"
        }
    }
"""
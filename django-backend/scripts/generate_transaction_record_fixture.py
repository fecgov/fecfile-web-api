import argparse
from secrets import choice

# Generate Transaction Record Fixture
#
#    Creates a json file containing valid transaction records
#    for the form_type values specified by the user, and with
#    randomly generated values for transaction_amount.


def get_arguments():
    parser = argparse.ArgumentParser(
        prog='Generate Transaction Record Fixture',
        description='Creates a json file containing valid transaction records\n'
                    + 'for the form_type values specified by the user and with\n'
                    + 'randomly generated values for transaction_amount.'
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
        '--report_a_id',
        default="b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
        help='primary report (default: b6d60d2d-d926-4e89-ad4b-c47d152a66ae)'
    )
    parser.add_argument(
        '--report_b_id',
        default="1406535e-f99f-42c4-97a8-247904b7d297",
        help='secondary report used for transactions outside of report dates'
            +' (default: 1406535e-f99f-42c4-97a8-247904b7d297)'
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
        '--transaction_type_identifier',
        default="Transaction Type Identifier",
        help='default value: Transaction Type Identifier'
    )
    parser.add_argument(
        '--output_file',
        help="Output to a file instead of the console (e.g --output_file=records.txt)")

    return parser.parse_args()


def get_schedule(form_type):
    schedule = str(form_type[1]).capitalize()  # the second char in the form_type
    if schedule == "C" and form_type[2] in ["1", "2"]:
        schedule = form_type[1:2]
    return schedule


def get_comment(form_type, test_case):
    if test_case == "within_dates":
        return f"{form_type} within report dates, should count in Col. A"
    if test_case == "within_year":
        return f"{form_type} within year, should count in Col. B"
    if test_case == "outside_dates":
        return f"{form_type} outside of dates, should not count"
    if test_case == "within_dates_but_memo":
        return f"{form_type} is a memo item, should not count"
    return ""


def get_amount_field(schedule):
    if schedule == "A":
        return "contribution_amount"
    if schedule == "B":
        return "expenditure_amount"
    if schedule == "C":
        return "loan_amount"
    if schedule == "C1":
        return "loan_amount"
    if schedule == "C2":
        return "guaranteed_amount"
    if schedule == "D":
        return "incurred_amount"
    if schedule == "E":
        return "expenditure_amount"
    return ""


def get_date_field(schedule):
    if schedule == "A":
        return "contribution_date"
    if schedule == "B":
        return "expenditure_date"
    if schedule == "C":
        return "loan_incurred_date"
    if schedule == "C1":
        return "loan_incurred_date"
    if schedule == "C2":
        return ""
    if schedule == "D":
        return ""
    if schedule == "E":
        return "disbursement_date"
    return ""


def get_date(args, test_case):
    report_start = args.report_start_date.split("-")
    report_end = args.report_end_date.split("-")

    if "within_dates" in test_case:
        return "-".join(report_start)

    if "year" in test_case:
        months = set([str(m).rjust(2, "0") for m in range(1, 13)])
        report_start_month = report_start[1]
        report_months = range(int(report_start_month), 13)
        formatted_report_months = set([str(m).rjust(2, "0") for m in report_months])
        months_before_report = list(months - formatted_report_months)
        if len(months_before_report) > 0:
            random_month = choice(months_before_report)
        else:
            random_month = report_start_month

        report_start_day = report_start[2]
        if (int(report_start_day) > 1):
            random_day = str(choice(range(1, int(report_start_day)))).rjust(2, "0")
        else:
            random_day = "01"

        if report_start_month == "01" and report_start_day == "01":
            raise ValueError(
                'Cannot set any date in same year before provided start date'
                + f' ({args.report_start_date})'
            )

        year = report_start[0]
        return f"{year}-{random_month}-{random_day}"

    report_years = set([report_start[0], report_end[0]])
    random_year = choice(list(set(range(2000 - 50, 2000 + 50)) - report_years))
    random_month = choice([str(m).rjust(2, "0") for m in range(1, 13)])
    return f"{random_year}-{random_month}-01"


def get_date_entry(date_field, date):
    if (len(date_field) > 0):
        return f''',\n{" "*12}"{date_field}": "{date}"'''
    return ""


def get_report_id(args, test_case):
    if "within_dates" in test_case:
        return args.report_a_id
    else:
        return args.report_b_id


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
    schedule_str += "0" + str(line_number)
    schedule_str = schedule_str.ljust(8, "0")

    record_str = str(record_number + 1).rjust(12, "0")

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

        comment = get_comment(form_type, test_case)

        schedule = get_schedule(form_type)
        schedule_model = f"schedule{schedule.lower()}"

        schedule_id = get_id(form_type, record_number, schedule)
        transaction_id = get_id(form_type, record_number, schedule)

        amount_field = get_amount_field(schedule)
        amount = choice(range(20, 150))

        date_field = get_date_field(schedule)
        date = get_date(args, test_case)
        date_entry = get_date_entry(date_field, date)

        report_id = get_report_id(args, test_case)

        memo_code = str(
            test_case == "within_dates_but_memo"
        ).lower()  # JSON uses lowercase true/false

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
            "report_id": "{report_id}",
            "_form_type": "{form_type}",
            "memo_code": {memo_code},
            "created": "2022-02-09T00:00:00.000Z",
            "updated": "2022-02-09T00:00:00.000Z",
            "transaction_type_identifier": {args.transaction_type_identifier}
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

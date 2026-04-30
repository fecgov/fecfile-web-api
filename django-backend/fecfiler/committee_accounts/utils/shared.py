import re


def is_valid_committee_id(committee_id):
    regex = re.compile(r"^C\d{8}$")
    match = regex.match(str(committee_id))
    return bool(match)

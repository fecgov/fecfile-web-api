import logging
from fecfiler import settings

logger = logging.getLogger(__name__)


def get_production_committee_raw_first(committee_id):
    """Queries the production FEC API for committee data
    First tries raw endpoint and then falls back to processed endpoint
    """
    raw_and_processed_endpoints = [
        f"{settings.PRODUCTION_OPEN_FEC_API}efile/form1/",
        f"{settings.PRODUCTION_OPEN_FEC_API}committee/{committee_id}/",
    ]
    params = {
        "api_key": settings.PRODUCTION_OPEN_FEC_API_KEY,
        "committee_id": committee_id,
    }
    return query_multiple_endpoints(raw_and_processed_endpoints, params)


def get_production_committee_processed_first(committee_id):
    """Queries the production FEC API for committee data
    First tries processed endpoint and then falls back to raw endpoint
    """
    processed_and_raw_endpoints = [
        f"{settings.PRODUCTION_OPEN_FEC_API}committee/{committee_id}/",
        f"{settings.PRODUCTION_OPEN_FEC_API}efile/form1/",
    ]
    params = {
        "api_key": settings.PRODUCTION_OPEN_FEC_API_KEY,
        "committee_id": committee_id,
    }
    return query_multiple_endpoints(processed_and_raw_endpoints, params)


def get_production_committee_emails(committee_id):
    """"""
    committee = get_production_committee_raw_first(committee_id)
    return committee.get("email", "") if committee else ""


def get_production_committee_data(committee_id):
    committee_data = get_production_committee_processed_first(committee_id)
    if committee_data is None:
        return None

    # Committee Type Label
    committee_data["committee_type_label"] = committee_data.get(
        "committee_type_full", None
    )

    # PAC/PTY
    committee_data["isPTY"] = is_production_efo_pty(committee_data)
    committee_data["isPAC"] = is_production_efo_pac(committee_data)

    # Qualified
    committee_data["qualified"] = (
        committee_data.get("committee_type") in PRODUCTION_QUALIFIED_COMMITTEES
    )

    return committee_data


def is_production_efo_pty(committee_data):
    designation = committee_data.get("designation", None)
    committee_type = committee_data.get("committee_type", None)
    return designation is not None and (
        committee_type == "Y" or (committee_type == "X" and designation != "U")
    )


def is_production_efo_pac(committee_data):
    return committee_data.get("committee_type") in PRODUCTION_PAC_COMMITTEE_TYPES

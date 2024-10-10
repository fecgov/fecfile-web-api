from fecfiler.settings import (
    FLAG__COMMITTEE_DATA_SOURCE,
    MOCK_OPENFEC_REDIS_URL,
    UNIT_TESTING_ENVIRONMENT
)
import json
import redis

COMMITTEE_DATA_REDIS_KEY = "COMMITTEE_DATA"
if FLAG__COMMITTEE_DATA_SOURCE == "REDIS" or UNIT_TESTING_ENVIRONMENT:
    redis_instance = redis.Redis.from_url(MOCK_OPENFEC_REDIS_URL)
else:
    redis_instance = None


def committee(committee_id):
    if redis_instance:
        committee_data = redis_instance.get(COMMITTEE_DATA_REDIS_KEY) or ""
        committees = json.loads(committee_data) or []
        committee = next(
            (
                committee
                for committee in committees
                if committee.get("committee_id") == committee_id
            ),
            None,
        )
        if committee:
            # rename key so we can use same mock data for both
            # query_filings and committee details endpoints
            committee['name'] = committee.pop('committee_name')
            return {  # same as api.open.fec.gov
                "api_version": "1.0",
                "results": [committee],
                "pagination": {
                    "pages": 1,
                    "per_page": 20,
                    "count": 1,
                    "page": 1,
                },
            }
        return None


def query_filings(query, form_type):
    if redis_instance:
        committee_data = redis_instance.get(COMMITTEE_DATA_REDIS_KEY) or ""
        committees = json.loads(committee_data or "[]")
        filtered_committee_data = [
            committee
            for committee in committees
            if query.upper() in committee.get("committee_id").upper()
            or query.upper() in committee.get("committee_name").upper()
        ]
        return {  # same as api.open.fec.gov
            "api_version": "1.0",
            "results": filtered_committee_data,
            "pagination": {"pages": 1, "per_page": 20, "count": 1, "page": 1},
        }


def recent_f1(committee_id):
    if redis_instance:
        committee_data = redis_instance.get(COMMITTEE_DATA_REDIS_KEY) or ""
        committees = json.loads(committee_data) or []
        return next(
            committee
            for committee in committees
            if committee.get("committee_id") == committee_id
        )

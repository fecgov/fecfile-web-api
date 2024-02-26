from fecfiler.settings import MOCK_OPENFEC_REDIS_URL
import json
import redis

COMMITTEE_DATA_REDIS_KEY = "COMMITTEE_DATA"
if MOCK_OPENFEC_REDIS_URL:
    redis_instance = redis.Redis.from_url(MOCK_OPENFEC_REDIS_URL)


def query_filings(query, form_type):
    if redis_instance:
        committee_data = redis_instance.get(COMMITTEE_DATA_REDIS_KEY) or ""
        committees = json.loads(committee_data) or []
        filtered_committee_data = [
            committee
            for committee in committees
            if query in committee.get("committee_id")
            or query in committee.get("committee_name")
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

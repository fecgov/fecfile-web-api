import os

from locust import HttpUser, between, task


def _profile_headers(group: str) -> dict:
    run_id = os.environ.get("FECFILE_PROFILE_RUN_ID")
    if not run_id:
        return {}
    return {
        "X-FECFILE-PROFILE-RUN-ID": run_id,
        "X-FECFILE-PROFILE-CLIENT": "locust",
        "X-FECFILE-PROFILE-GROUP": group,
    }


class ProfiledApiUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def openapi_schema(self):
        self.client.get("/api/schema", headers=_profile_headers("schema"), name="schema")

    @task
    def openapi_docs(self):
        self.client.get("/api/docs", headers=_profile_headers("docs"), name="docs")

"""Load testing for the FECFile API and web app. Run from command directory using the

`docker-compose --profile locust up -d`

Go to http://0.0.0.0:8089/ to run tests.


Run on other spaces:
Log in to that environment, and get the session ID from the header and update the
OIDC_SESSION_ID environment variable on your local machine

Modifying docker-compose:
-f /mnt/locust/locustfile.py --master -H https://fecfile-web-api-dev.app.cloud.gov



Scale up using docker:
docker-compose --profile locust up -d --scale locust-follower=4

Environment variables:
Ask team about what to set for
`LOCAL_TEST_USER` and `LOCAL_TEST_PWD`

Get `OIDC_SESSION_ID` from an authenticated sesion

"""

import os
import resource
import logging
import random

from locust import between, task, TaskSet, user

TEST_USER = os.environ.get("LOCAL_TEST_USER")
TEST_PWD = os.environ.get("LOCAL_TEST_PWD")
SESSION_ID = os.environ.get("OIDC_SESSION_ID")

SCHEDULES = ["A", "B,E", "C,D"]


# As of 11/2023 max time for successful queries is about 30 sec
timeout = 30

# Avoid "Too many open files" error
resource.setrlimit(resource.RLIMIT_NOFILE, (10000, 999999))


class Tasks(TaskSet):

    def on_start(self):
        if "cloud.gov" in self.client.base_url:
            self.client.headers = {
                "cookie": f"sessionid={SESSION_ID};",
                "user-agent": "Locust testing",
            }
        else:
            self.client.post(
                "/user/login/authenticate",
                json={"username": TEST_USER, "password": TEST_PWD}
            )
        self.reports = self.fetch_ids("reports", "id")

    def fetch_ids(self, endpoint, key):
        response = self.client.get(f"/api/v1/{endpoint}", name="preload_ids")
        if response.status_code == 200:
            return [result[key] for result in response.json()["results"]]
        else:
            logging.error(f"{response.status_code} error fetching pre-load id")

    @task
    def celery_test(self):
        self.client.get(
            "/celery-test/",
            name="celery-test",
            timeout=timeout
        )

    @task
    def load_contacts(self):
        params = {
            "page": 1,
            "ordering": "form_type",
        }
        self.client.get(
            "/api/v1/contacts/",
            name="load_contacts",
            timeout=timeout,
            params=params
        )

    @task
    def load_reports(self):
        params = {
            "page": 1,
            "ordering": "form_type",
        }
        self.client.get(
            "/api/v1/reports/",
            name="load_reports",
            timeout=timeout,
            params=params
        )

    @task
    def load_transactions(self):
        report_id = random.choice(self.reports)
        schedules = random.choice(SCHEDULES)
        params = {
            "page": 1,
            "ordering": "form_type",
            "schedules": schedules,
            "report_id": report_id,
        }
        self.client.get(
            "/api/v1/transactions/",
            name="load_transactions",
            timeout=timeout,
            params=params
        )


class Swarm(user.HttpUser):
    tasks = [Tasks]
    wait_time = between(1, 5)

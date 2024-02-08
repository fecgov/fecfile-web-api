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

from locust import between, task, TaskSet, user

TEST_USER = os.environ.get("LOCAL_TEST_USER")
TEST_PWD = os.environ.get("LOCAL_TEST_PWD")
SESSION_ID = os.environ.get("OIDC_SESSION_ID")


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

    @task
    def celery_test(self):

        self.client.get(
            "/celery-test/",
            name="celery-test",
            timeout=timeout
        )


class Swarm(user.HttpUser):
    tasks = [Tasks]
    wait_time = between(1, 5)

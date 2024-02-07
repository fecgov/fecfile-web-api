"""Load testing for the FECFile API and web app. Run from command directory using the

`docker-compose --profile locust up -d`

Go to http://0.0.0.0:8089/ to run tests.


Run on other spaces by modifying docker-compose:
-f /mnt/locust/locustfile.py --master -H https://fecfile-web-api-dev.app.cloud.gov/api/v1

Scale up using docker:

`docker-compose --profile locust up -d` --scale locust-follower=4`

API keys:
Ask team about what to set for
`LOCAL_TEST_USER` and `LOCAL_TEST_PWD`

"""

import os
import resource

from locust import between, task, TaskSet, user

TEST_USER = os.environ["LOCAL_TEST_USER"]
TEST_PWD = os.environ["LOCAL_TEST_PWD"]


# As of 11/2023 max time for successful queries is about 30 sec
timeout = 30

# Avoid "Too many open files" error
resource.setrlimit(resource.RLIMIT_NOFILE, (10000, 999999))


class Tasks(TaskSet):
    def on_start(self):
        self.client.post(
            "/user/login/authenticate",
            json={"username": TEST_USER, "password": TEST_PWD}
        )

    @task
    def celery_test(self):
        params = {"api_key": "DEMO_KEY"}
        self.client.get(
            "/celery-test/",
            name="celery-test",
            params=params,
            timeout=timeout
        )


class Swarm(user.HttpUser):
    tasks = [Tasks]
    wait_time = between(1, 5)

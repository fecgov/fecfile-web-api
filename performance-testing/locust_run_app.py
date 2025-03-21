from locust import task, TaskSet, user, between


POLLING_INTERVAL = 5  # Seconds between requests made to /index.html
POLLING_DEVIATION = 0.1  # Variation, measured in seconds in requests

# A slight variation is applied between requests because real-world users
# won't all be aligned to exact 1,000ms intervals.


class Tasks(TaskSet):

    @task
    def get_index_html(self):
        with self.client.get("/index.html", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Non-200 return")


class Swarm(user.HttpUser):
    tasks = [Tasks]
    wait_time = between(
        POLLING_INTERVAL - POLLING_DEVIATION,
        POLLING_INTERVAL + POLLING_DEVIATION
    )

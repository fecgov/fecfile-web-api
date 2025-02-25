import os
import resource
import logging
import random
import json
import math

from locust import task, TaskSet, user, between


class Tasks(TaskSet):

    @task
    def get_index_html(self):
        self.client.get(
            "/index.html", allow_redirects=False
        )


class Swarm(user.HttpUser):
    tasks = [Tasks]
    wait_time = between(4.5, 5.5)

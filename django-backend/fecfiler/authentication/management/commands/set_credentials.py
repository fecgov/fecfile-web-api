from django.core.management.base import BaseCommand
import requests


class Command(BaseCommand):
    help = "Set credentials in cloud foundry"
    base_uri = "https://api.fr.cloud.gov/v3"

    def add_arguments(self, parser):
        parser.add_argument("space", type=str)
        parser.add_argument("service_instance_name", type=str)
        parser.add_argument("token", type=str)
        parser.add_argument("credentials_dict", type=dict)

    def handle(self, *args, **options):
        try:
            space = options["space"]
            service_instance_name = options["service_instance_name"]
            token = options["token"]
            credentials_dict = options["credentials_dict"]

            self.stdout.write(self.style.NOTICE("Retrieving guid for space"))
            space_guid = self.get_space_guid(token, space)
        except Exception:
            self.stdout.write(
                self.style.ERROR(
                    "Failed to set credentials for space "
                    f"{space} service_instance_name {service_instance_name}"
                )
            )

    def get_space_guid(self, token, space):
        try:
            space_guid = ""
            header = {
                "Authorization": token,
            }
            data = {
                "names": [
                    space.lower(),
                ]
            }
            url = f"{self.base_uri}/spaces"
            response = requests.get(url, params=data, headers=header)
            response.raise_for_status()
            response_json = response.json()
            if response_json["resources"][0]["name"] == space.lower():
                space_guid = response_json["resources"][0]["guid"]
            if space_guid == "":
                raise Exception("Space guid not found")
            return space_guid
        except:
            self.stdout.write(
                self.style.ERROR(f"Failed to retrieving guid for space {space}")
            )
            raise

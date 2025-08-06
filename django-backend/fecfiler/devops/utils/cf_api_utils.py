import requests
import structlog

logger = structlog.get_logger(__name__)

base_uri = "https://api.fr.cloud.gov/v3"


def check_api_status():
    try:
        url = base_uri
        response = requests.get(url)
        response.raise_for_status()
        return response
    except Exception as e:
        raise Exception("Failed to retrieve api status") from e


def retrieve_credentials(token, organization_name, space_name, service_instance_name):
    try:
        logger.info(f"Retrieving guid for service_instance_name {service_instance_name}")
        service_instance_guid = get_service_instance_guid_from_names(
            token, organization_name, space_name, service_instance_name
        )

        logger.info(f"Retrieving creds for service_instance_guid {service_instance_guid}")
        return get_credentials_by_guid(token, service_instance_guid)
    except Exception as e:
        raise Exception(
            "FAILED to retrieve credentials for "
            f"organization_name {organization_name} "
            f"space_name {space_name} "
            f"service_instance_name {service_instance_name}"
        ) from e


def update_credentials(
    token, organization_name, space_name, service_instance_name, credentials_dict
):
    try:
        logger.info(f"Retrieving guid for service_instance_name {service_instance_name}")
        service_instance_guid = get_service_instance_guid_from_names(
            token, organization_name, space_name, service_instance_name
        )

        logger.info(f"Retrieving creds for service_instance_guid {service_instance_guid}")
        creds = get_credentials_by_guid(token, service_instance_guid)

        logger.info("Merging creds")
        merged_creds = merge_credentials(creds, credentials_dict)

        logger.info(f"Updating creds for service_instance_guid {service_instance_guid}")
        update_credentials_for_service(token, service_instance_guid, merged_creds)
    except Exception as e:
        raise Exception(
            "FAILED to update credentials for "
            f"organization_name {organization_name} "
            f"space_name {space_name} "
            f"service_instance_name {service_instance_name}"
        ) from e


def get_auth_header(token):
    return {
        "Authorization": token,
    }


def get_organization_guid(token, organization_name):
    try:
        organization_guid = ""
        data = {
            "names": [
                organization_name,
            ]
        }
        url = f"{base_uri}/organizations"
        response = requests.get(url, params=data, headers=get_auth_header(token))
        response.raise_for_status()
        response_json = response.json()
        if response_json["resources"][0]["name"] == organization_name:
            organization_guid = response_json["resources"][0]["guid"]
        if organization_guid == "":
            raise Exception("Organization guid not found in response")
        return organization_guid
    except Exception as e:
        raise Exception(
            f"Failed to retrieve guid for organization_name {organization_name}"
        ) from e


def get_space_guid(token, space_name, organization_guid):
    try:
        space_guid = ""
        data = {
            "names": [
                space_name,
            ],
            "organization_guids": [
                organization_guid,
            ],
        }
        url = f"{base_uri}/spaces"
        response = requests.get(url, params=data, headers=get_auth_header(token))
        response.raise_for_status()
        response_json = response.json()
        if response_json["resources"][0]["name"] == space_name:
            space_guid = response_json["resources"][0]["guid"]
        if space_guid == "":
            raise Exception("Space guid not found in response")
        return space_guid
    except Exception as e:
        raise Exception(f"Failed to retrieve guid for space_name {space_name}") from e


def get_service_instance_guid_from_names(
    token, organization_name, space_name, service_instance_name
):
    try:
        logger.info(f"Retrieving guid for organization_name {organization_name}")
        organization_guid = get_organization_guid(token, organization_name)

        logger.info(f"Retrieving guid for space_name {space_name}")
        space_guid = get_space_guid(token, space_name, organization_guid)

        logger.info(f"Retrieving guid for service_instance_name {service_instance_name}")
        service_instance_guid = get_service_instance_guid(
            token, organization_guid, space_guid, service_instance_name
        )

        return service_instance_guid
    except Exception as e:
        raise Exception(
            "Failed to retrieve service_instance_guid by names for "
            f"{organization_name} organization_name "
            f"{space_name} space_name "
            f"{service_instance_name} service_instance_name"
        ) from e


def get_service_instance_guid(
    token, organization_guid, space_guid, service_instance_name
):
    try:
        service_instance_guid = ""
        data = {
            "names": [
                service_instance_name,
            ],
            "space_guids": [
                space_guid,
            ],
            "organization_guids": [
                organization_guid,
            ],
        }
        url = f"{base_uri}/service_instances"
        response = requests.get(url, params=data, headers=get_auth_header(token))
        response.raise_for_status()
        response_json = response.json()
        if response_json["resources"][0]["name"] == service_instance_name:
            service_instance_guid = response_json["resources"][0]["guid"]
        if service_instance_guid == "":
            raise Exception("Service instance guid not found in response")
        return service_instance_guid
    except Exception as e:
        raise Exception(
            "Failed to retrieve service_instance_guid by guids for "
            f"{organization_guid} organization_guid "
            f"{space_guid} space_guid "
            f"{service_instance_name} service_instance_name"
        ) from e


def get_credentials_by_guid(token, service_instance_guid):
    try:
        url = f"{base_uri}/service_instances/{service_instance_guid}/credentials"
        response = requests.get(url, headers=get_auth_header(token))
        response.raise_for_status()
        creds = response.json()
        return creds
    except Exception as e:
        raise Exception(
            "Failed to retrieve creds for service_instance_guid "
            f"{service_instance_guid}"
        ) from e


def merge_credentials(creds, update_data):
    creds.update(update_data)
    return {"credentials": creds}


def update_credentials_for_service(token, service_instance_guid, creds):
    try:
        headers = get_auth_header(token) | {"Content-Type": "application/json"}
        url = f"{base_uri}/service_instances/{service_instance_guid}"
        response = requests.patch(url, json=creds, headers=headers)
        response.raise_for_status()
    except Exception as e:
        raise Exception(
            "Failed to patch creds for service_instance_guid " f"{service_instance_guid}"
        ) from e

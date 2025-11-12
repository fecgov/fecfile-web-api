from fecfiler.devops.utils.cf_api import retrieve_credentials, update_credentials
from django.core.management.utils import get_random_secret_key
import structlog

logger = structlog.get_logger(__name__)


def gen_and_install_django_key(
    cf_token: str,
    cf_organization_name: str,
    cf_space_name: str,
    cf_service_instance_name: str,
):
    try:
        logger.info("Generating key")
        key = get_random_secret_key()

        logger.info("Retrieving current creds")
        current_creds = retrieve_credentials(
            cf_token, cf_organization_name, cf_space_name, cf_service_instance_name
        )

        logger.info("Installing key")
        updated_keys = {
            "DJANGO_SECRET_KEY_FALLBACKS": [
                *(current_creds.get("DJANGO_SECRET_KEY_FALLBACKS", [])),
                current_creds["DJANGO_SECRET_KEY"],
            ],
            "DJANGO_SECRET_KEY": key,
        }
        update_credentials(
            cf_token,
            cf_organization_name,
            cf_space_name,
            cf_service_instance_name,
            updated_keys,
        )
    except Exception as e:
        raise Exception("Failed to generate and install django key") from e


def clear_fallback_django_keys(
    cf_token: str,
    cf_organization_name: str,
    cf_space_name: str,
    cf_service_instance_name: str,
):
    try:
        creds_to_update = {"DJANGO_SECRET_KEY_FALLBACKS": []}
        update_credentials(
            cf_token,
            cf_organization_name,
            cf_space_name,
            cf_service_instance_name,
            creds_to_update,
        )
    except Exception as e:
        raise Exception("Failed to clear fallback django keys") from e

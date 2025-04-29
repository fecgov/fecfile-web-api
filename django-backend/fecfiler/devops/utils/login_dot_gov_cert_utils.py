from fecfiler.settings import (
    AWS_STORAGE_BUCKET_NAME,
    LOGIN_DOT_GOV_X509_COUNTRY,
    LOGIN_DOT_GOV_X509_STATE,
    LOGIN_DOT_GOV_X509_LOCALITY,
    LOGIN_DOT_GOV_X509_ORG,
    LOGIN_DOT_GOV_X509_ORG_UNIT,
    LOGIN_DOT_GOV_X509_COMMON_NAME,
    LOGIN_DOT_GOV_X509_EMAIL_ADDRESS,
    LOGIN_DOT_GOV_X509_DAYS_VALID,
    LOGIN_DOT_GOV_RSA_PK_SIZE,
)
from fecfiler.s3 import S3_SESSION
from fecfiler.devops.utils.cf_api_utils import retrieve_credentials, update_credentials
from fecfiler.devops.utils.crypt_utils import (
    gen_rsa_pk,
    rsa_pk_to_bytes,
    gen_x509_cert,
    x509_cert_to_bytes,
)
from cryptography.x509 import Certificate
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timezone
import structlog

logger = structlog.get_logger(__name__)


def backout_login_dot_gov_cert(
    cf_token: str,
    cf_organization_name: str,
    cf_space_name: str,
    cf_service_instance_name: str,
):
    try:
        logger.info("Retrieving current creds")
        current_creds = retrieve_credentials(
            cf_token, cf_organization_name, cf_space_name, cf_service_instance_name
        )

        logger.info("Backing out creds")
        updated_keys = {
            "OIDC_RP_CLIENT_SECRET_STAGING": current_creds["OIDC_RP_CLIENT_SECRET"],
            "OIDC_RP_CLIENT_SECRET": current_creds["OIDC_RP_CLIENT_SECRET_BACKUP"],
        }
        update_credentials(
            cf_token,
            cf_organization_name,
            cf_space_name,
            cf_service_instance_name,
            updated_keys,
        )
    except Exception as e:
        raise Exception("Failed backout login dot gov cert") from e


def install_login_dot_gov_cert(
    cf_token: str,
    cf_organization_name: str,
    cf_space_name: str,
    cf_service_instance_name: str,
):
    try:
        logger.info("Retrieving current creds")
        current_creds = retrieve_credentials(
            cf_token, cf_organization_name, cf_space_name, cf_service_instance_name
        )

        logger.info("Updating creds")
        updated_keys = {
            "OIDC_RP_CLIENT_SECRET_BACKUP": current_creds["OIDC_RP_CLIENT_SECRET"],
            "OIDC_RP_CLIENT_SECRET": current_creds["OIDC_RP_CLIENT_SECRET_STAGING"],
        }
        update_credentials(
            cf_token,
            cf_organization_name,
            cf_space_name,
            cf_service_instance_name,
            updated_keys,
        )
    except Exception as e:
        raise Exception("Failed install login dot gov cert") from e


def gen_and_stage_login_dot_gov_cert(
    cf_token: str,
    cf_organization_name: str,
    cf_space_name: str,
    cf_service_instance_name: str,
):
    try:
        logger.info("Generating rsa pk")
        rsa_pk = gen_rsa_pk(LOGIN_DOT_GOV_RSA_PK_SIZE)

        logger.info("Generating x509 cert")
        x509_cert = gen_x509_cert(
            LOGIN_DOT_GOV_X509_COUNTRY,
            LOGIN_DOT_GOV_X509_STATE,
            LOGIN_DOT_GOV_X509_LOCALITY,
            LOGIN_DOT_GOV_X509_ORG,
            LOGIN_DOT_GOV_X509_ORG_UNIT,
            LOGIN_DOT_GOV_X509_COMMON_NAME,
            LOGIN_DOT_GOV_X509_EMAIL_ADDRESS,
            LOGIN_DOT_GOV_X509_DAYS_VALID,
            rsa_pk,
        )

        logger.info("Staging login.gov cert")
        stage_login_dot_gov_cert(x509_cert)

        logger.info("Staging login.gov pk")
        stage_login_dot_gov_pk(
            cf_token,
            cf_organization_name,
            cf_space_name,
            cf_service_instance_name,
            rsa_pk,
        )
    except Exception as e:
        raise Exception("Failed to generate and stage cert") from e


def stage_login_dot_gov_pk(
    cf_token: str,
    cf_organization_name: str,
    cf_space_name: str,
    cf_service_instance_name: str,
    rsa_pk: rsa.RSAPrivateKey,
):
    try:
        rsa_pk_creds_bytes = rsa_pk_to_bytes(rsa_pk)
        creds_to_update = {"OIDC_RP_CLIENT_SECRET_STAGING": rsa_pk_creds_bytes.decode()}
        update_credentials(
            cf_token,
            cf_organization_name,
            cf_space_name,
            cf_service_instance_name,
            creds_to_update,
        )
    except Exception:
        raise Exception("Failed stage login dot gov pk")


def stage_login_dot_gov_cert(x509_cert: Certificate):
    try:
        x509_cert_bytes = x509_cert_to_bytes(x509_cert)
        filename = (
            f"gen_x509_pk_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.crt"
        )
        s3_object = S3_SESSION.Object(AWS_STORAGE_BUCKET_NAME, filename)
        s3_object.put(Body=x509_cert_bytes)
        logger.info(f"Cert saved as {filename}")
    except Exception:
        raise Exception("Failed stage login dot gov cert")


def cleanup_login_dot_gov_certs():
    try:
        logger.info("Cleaning up certs")
        bucket = S3_SESSION.Bucket(AWS_STORAGE_BUCKET_NAME)
        bucket.objects.filter(Prefix="gen_x509_pk_").delete()
    except Exception as e:
        raise Exception("Failed cleanup login dot x509 certs") from e

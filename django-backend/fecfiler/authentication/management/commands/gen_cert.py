from django.core.management.base import BaseCommand
from fecfiler.settings import (
    MOCK_OPENFEC_REDIS_URL,
    BASE_DIR,
    AWS_STORAGE_BUCKET_NAME,
    LOGIN_DOT_GOV_RSA_PK_SIZE,
    LOGIN_DOT_GOV_X509_DAYS_VALID,
    LOGIN_DOT_GOV_X509_COUNTRY,
    LOGIN_DOT_GOV_X509_STATE,
    LOGIN_DOT_GOV_X509_LOCALITY,
    LOGIN_DOT_GOV_X509_ORG,
    LOGIN_DOT_GOV_X509_ORG_UNIT,
    LOGIN_DOT_GOV_X509_COMMON_NAME,
    LOGIN_DOT_GOV_X509_EMAIL_ADDRESS,
)
from fecfiler.s3 import S3_SESSION
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
import datetime


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--s3", action="store_true")

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.NOTICE("Generating rsa pk.."))
            rsa_pk = self.gen_rsa_pk()
            self.stdout.write(self.style.NOTICE("Generating x509 cert.."))
            x509_cert = self.gen_x509_cert(rsa_pk)
            self.stdout.write(self.style.SUCCESS("Successfully generated pk/cert"))
        except Exception:
            self.stdout.write(self.style.SUCCESS("Failed to generated pk/cert"))

    def gen_rsa_pk(self):
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=LOGIN_DOT_GOV_RSA_PK_SIZE,
        )

    def gen_x509_cert(self, rsa_pk: rsa.RSAPrivateKey):
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, LOGIN_DOT_GOV_X509_COUNTRY),
                x509.NameAttribute(
                    NameOID.STATE_OR_PROVINCE_NAME, LOGIN_DOT_GOV_X509_STATE
                ),
                x509.NameAttribute(NameOID.LOCALITY_NAME, LOGIN_DOT_GOV_X509_LOCALITY),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, LOGIN_DOT_GOV_X509_ORG),
                x509.NameAttribute(
                    NameOID.ORGANIZATIONAL_UNIT_NAME, LOGIN_DOT_GOV_X509_ORG_UNIT
                ),
                x509.NameAttribute(NameOID.COMMON_NAME, LOGIN_DOT_GOV_X509_COMMON_NAME),
                x509.NameAttribute(
                    NameOID.EMAIL_ADDRESS, LOGIN_DOT_GOV_X509_EMAIL_ADDRESS
                ),
            ]
        )
        return (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(rsa_pk.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
            .not_valid_after(
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=LOGIN_DOT_GOV_X509_DAYS_VALID)
            )
            .sign(rsa_pk, hashes.SHA256())
        )

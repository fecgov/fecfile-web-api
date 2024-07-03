from cryptography import x509
from cryptography.x509 import Certificate
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization
import datetime
import structlog

logger = structlog.get_logger(__name__)


def gen_rsa_pk(size: int):
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=size,
    )


def rsa_pk_to_bytes(rsa_pk: rsa.RSAPrivateKey):
    return rsa_pk.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def gen_x509_cert(
    country: str,
    state: str,
    locality: str,
    org: str,
    org_unit: str,
    common_name: str,
    email_address: str,
    days_valid: float,
    rsa_pk: rsa.RSAPrivateKey,
):
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, org_unit),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, email_address),
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
            + datetime.timedelta(days=days_valid)
        )
        .sign(rsa_pk, hashes.SHA256())
    )


def x509_cert_to_bytes(x509_cert: Certificate):
    return x509_cert.public_bytes(serialization.Encoding.PEM)

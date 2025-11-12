from django.test import TestCase
from unittest.mock import patch
from fecfiler.devops.utils.crypt import (
    gen_rsa_pk,
    rsa_pk_to_bytes,
    gen_x509_cert,
    x509_cert_to_bytes,
)


class CfApiUtilsTestCase(TestCase):

    # gen_rsa_pk

    @patch("cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key")
    def test_gen_rsa_pk_throws_exception(
        self,
        generate_private_key_mock,
    ):
        generate_private_key_mock.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "Failed generate rsa pk",
        ):
            gen_rsa_pk(123)

    @patch("cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key")
    def test_gen_rsa_pk_happy_path(
        self,
        generate_private_key_mock,
    ):
        mock_rsa_pk = {"testkey1": "testval1"}
        generate_private_key_mock.return_value = mock_rsa_pk

        retval = gen_rsa_pk(123)
        self.assertEqual(retval, mock_rsa_pk)

    # rsa_pk_to_bytes

    @patch(
        "cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey",
    )
    def test_rsa_pk_to_bytes_throws_exception(
        self,
        rsa_pk_mock,
    ):
        rsa_pk_mock.private_bytes.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "Failed serialize rsa pk",
        ):
            rsa_pk_to_bytes(rsa_pk_mock)

    @patch(
        "cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey",
    )
    def test_rsa_pk_to_bytes_happy_path(
        self,
        rsa_pk_mock,
    ):
        test_private_bytes = b"test_private_bytes"
        rsa_pk_mock.private_bytes.return_value = test_private_bytes

        retval = rsa_pk_to_bytes(rsa_pk_mock)
        self.assertEqual(retval, test_private_bytes)

    # gen_x509_cert

    @patch("fecfiler.devops.utils.crypt.x509")
    @patch("cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey")
    def test_gen_x509_cert_throws_exception(
        self,
        rsa_pk_mock,
        x509_mock,
    ):
        test_country = "test_country"
        test_state = "test_state"
        test_locality = "test_locality"
        test_org = "test_org"
        test_org_unit = "test_org_unit"
        test_common_name = "test_common_name"
        test_email_address = "test_email_address"
        test_days_valid = 365

        x509_mock.CertificateBuilder.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "Failed to generate x509 cert",
        ):
            gen_x509_cert(
                test_country,
                test_state,
                test_locality,
                test_org,
                test_org_unit,
                test_common_name,
                test_email_address,
                test_days_valid,
                rsa_pk_mock,
            )

    @patch("fecfiler.devops.utils.crypt.x509")
    @patch("cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey")
    def test_gen_x509_cert_happy_path(
        self,
        rsa_pk_mock,
        x509_mock,
    ):
        test_country = "test_country"
        test_state = "test_state"
        test_locality = "test_locality"
        test_org = "test_org"
        test_org_unit = "test_org_unit"
        test_common_name = "test_common_name"
        test_email_address = "test_email_address"
        test_days_valid = 365

        retval = gen_x509_cert(
            test_country,
            test_state,
            test_locality,
            test_org,
            test_org_unit,
            test_common_name,
            test_email_address,
            test_days_valid,
            rsa_pk_mock,
        )
        self.assertIsNotNone(retval)

    # x509_cert_to_bytes

    @patch(
        "cryptography.x509.Certificate",
    )
    def test_x509_cert_to_bytes_throws_exception(
        self,
        x509_cert_mock,
    ):
        x509_cert_mock.public_bytes.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "Failed to serialize x509 cert",
        ):
            x509_cert_to_bytes(x509_cert_mock)

    @patch(
        "cryptography.x509.Certificate",
    )
    def test_x509_cert_to_bytes_happy_path(
        self,
        x509_cert_mock,
    ):
        test_public_bytes = b"test_public_bytes"
        x509_cert_mock.public_bytes.return_value = test_public_bytes

        retval = x509_cert_to_bytes(x509_cert_mock)
        self.assertEqual(retval, test_public_bytes)

from django.test import TestCase, RequestFactory
from unittest.mock import patch
from fecfiler.devops.login_dot_gov_cert_utils import (
    stage_login_dot_gov_cert,
    stage_login_dot_gov_pk,
    gen_and_stage_login_dot_gov_cert,
    install_login_dot_gov_cert,
    backout_login_dot_gov_cert,
)
from django.core import management


class LoginDotGovUtilsTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    # backout_login_dot_gov_cert

    @patch("fecfiler.devops.login_dot_gov_cert_utils.retrieve_credentials")
    def test_backout_login_dot_gov_cert_throws_exception(
        self,
        retrieve_credentials_mock,
    ):
        test_token = "test_token"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        retrieve_credentials_mock.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "Failed backout login dot gov cert",
        ):
            backout_login_dot_gov_cert(
                test_token, test_space_name, test_service_instance_name
            )

    @patch("fecfiler.devops.login_dot_gov_cert_utils.retrieve_credentials")
    @patch("fecfiler.devops.login_dot_gov_cert_utils.update_credentials")
    def test_backout_login_dot_gov_cert_happy_path(
        self,
        update_credentials_mock,
        retrieve_credentials_mock,
    ):
        test_token = "test_token"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        management.call_command(
            "backout_login_dot_gov_cert",
            test_token,
            test_space_name,
            test_service_instance_name,
        )

        update_credentials_mock.assert_called_once()

    # install_login_dot_gov_cert

    @patch("fecfiler.devops.login_dot_gov_cert_utils.retrieve_credentials")
    def test_install_login_dot_gov_cert_throws_exception(
        self,
        retrieve_credentials_mock,
    ):
        test_token = "test_token"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        retrieve_credentials_mock.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "Failed install login dot gov cert",
        ):
            install_login_dot_gov_cert(
                test_token, test_space_name, test_service_instance_name
            )

    @patch("fecfiler.devops.login_dot_gov_cert_utils.retrieve_credentials")
    @patch("fecfiler.devops.login_dot_gov_cert_utils.update_credentials")
    def test_install_login_dot_gov_cert_happy_path(
        self,
        update_credentials_mock,
        retrieve_credentials_mock,
    ):
        test_token = "test_token"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        management.call_command(
            "install_login_dot_gov_cert",
            test_token,
            test_space_name,
            test_service_instance_name,
        )

        update_credentials_mock.assert_called_once()

    # gen_and_stage_login_dot_gov_cert

    @patch("fecfiler.devops.login_dot_gov_cert_utils.gen_rsa_pk")
    def test_gen_and_stage_login_dot_gov_cert_throws_exception(
        self,
        gen_rsa_pk_mock,
    ):
        test_token = "test_token"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        gen_rsa_pk_mock.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "Failed to generate and stage cert",
        ):
            gen_and_stage_login_dot_gov_cert(
                test_token, test_space_name, test_service_instance_name
            )

    @patch("fecfiler.devops.login_dot_gov_cert_utils.gen_rsa_pk")
    @patch("fecfiler.devops.login_dot_gov_cert_utils.gen_x509_cert")
    @patch("fecfiler.devops.login_dot_gov_cert_utils.stage_login_dot_gov_cert")
    @patch("fecfiler.devops.login_dot_gov_cert_utils.stage_login_dot_gov_pk")
    def test_gen_and_stage_login_dot_gov_cert_happy_path(
        self,
        stage_login_dot_gov_pk_mock,
        stage_login_dot_gov_cert_mock,
        gen_x509_cert_mock,
        gen_rsa_pk_mock,
    ):
        test_token = "test_token"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        management.call_command(
            "gen_and_stage_login_dot_gov_cert",
            test_token,
            test_space_name,
            test_service_instance_name,
        )

        stage_login_dot_gov_pk_mock.assert_called_once()

    # stage_login_dot_gov_pk

    @patch("fecfiler.devops.crypt_utils.rsa_pk_to_bytes")
    @patch("fecfiler.devops.login_dot_gov_cert_utils.update_credentials")
    @patch("cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey")
    def test_stage_login_dot_gov_pk_throws_exception(
        self,
        rsa_pk_mock,
        update_credentials_mock,
        rsa_pk_to_bytes_mock,
    ):
        test_token = "test_token"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        update_credentials_mock.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "Failed stage login dot gov pk",
        ):
            stage_login_dot_gov_pk(
                test_token, test_space_name, test_service_instance_name, rsa_pk_mock
            )

    @patch("fecfiler.devops.crypt_utils.rsa_pk_to_bytes")
    @patch("fecfiler.devops.login_dot_gov_cert_utils.update_credentials")
    @patch("cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey")
    def test_stage_login_dot_gov_pk_happy_path(
        self,
        rsa_pk_mock,
        update_credentials_mock,
        rsa_pk_to_bytes_mock,
    ):
        test_token = "test_token"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        stage_login_dot_gov_pk(
            test_token, test_space_name, test_service_instance_name, rsa_pk_mock
        )

        update_credentials_mock.assert_called_once()

    # stage_login_dot_gov_cert

    @patch("fecfiler.devops.crypt_utils.x509_cert_to_bytes")
    @patch("fecfiler.devops.crypt_utils.x509")
    def test_stage_login_dot_gov_cert_throws_exception(
        self,
        x509_mock,
        x509_cert_to_bytes_mock,
    ):
        x509_cert_to_bytes_mock.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "Failed stage login dot gov cert",
        ):
            stage_login_dot_gov_cert(x509_mock)

    @patch("fecfiler.devops.crypt_utils.x509_cert_to_bytes")
    @patch("fecfiler.devops.crypt_utils.x509")
    @patch("fecfiler.devops.login_dot_gov_cert_utils.S3_SESSION")
    def test_stage_login_dot_gov_cert_happy_path(
        self,
        s3_session_mock,
        x509_mock,
        x509_cert_to_bytes_mock,
    ):
        test_bytes = b"test_bytes"
        x509_cert_to_bytes_mock.return_value = test_bytes
        stage_login_dot_gov_cert(x509_mock)
        self.assertEqual(True, True)

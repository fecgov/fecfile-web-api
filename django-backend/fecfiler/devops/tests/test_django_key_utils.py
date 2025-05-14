from django.test import TestCase, RequestFactory
from unittest.mock import patch
from fecfiler.devops.utils.django_key_utils import (
    gen_and_install_django_key,
    clear_fallback_django_keys,
)
from django.core import management


class DjangoKeyUtilsTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    # gen_and_install_django_key

    @patch("fecfiler.devops.utils.django_key_utils.retrieve_credentials")
    def test_gen_and_install_django_key_throws_exception(
        self,
        retrieve_credentials_mock,
    ):
        test_token = "test_token"
        test_organization_name = "test_organization_name"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        retrieve_credentials_mock.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "Failed to generate and install django key",
        ):
            gen_and_install_django_key(
                test_token,
                test_organization_name,
                test_space_name,
                test_service_instance_name,
            )

    @patch("fecfiler.devops.utils.django_key_utils.retrieve_credentials")
    @patch("fecfiler.devops.utils.django_key_utils.update_credentials")
    def test_gen_and_install_django_key_happy_path(
        self,
        update_credentials_mock,
        retrieve_credentials_mock,
    ):
        test_token = "test_token"
        test_organization_name = "test_organization_name"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        management.call_command(
            "gen_and_install_django_key",
            test_token,
            test_organization_name,
            test_space_name,
            test_service_instance_name,
        )

        update_credentials_mock.assert_called_once()

    # clear_fallback_django_keys

    @patch("fecfiler.devops.utils.django_key_utils.update_credentials")
    def test_clear_fallback_django_keys_throws_exception(
        self,
        update_credentials_mock,
    ):
        test_token = "test_token"
        test_organization_name = "test_organization_name"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        update_credentials_mock.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "Failed to clear fallback django keys",
        ):
            clear_fallback_django_keys(
                test_token,
                test_organization_name,
                test_space_name,
                test_service_instance_name,
            )

    @patch("fecfiler.devops.utils.django_key_utils.update_credentials")
    def test_clear_fallback_django_keys_happy_path(
        self,
        update_credentials_mock,
    ):
        test_token = "test_token"
        test_organization_name = "test_organization_name"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        management.call_command(
            "clear_fallback_django_keys",
            test_token,
            test_organization_name,
            test_space_name,
            test_service_instance_name,
        )

        update_credentials_mock.assert_called_once_with(
            test_token,
            test_organization_name,
            test_space_name,
            test_service_instance_name,
            {"DJANGO_SECRET_KEY_FALLBACKS": []},
        )

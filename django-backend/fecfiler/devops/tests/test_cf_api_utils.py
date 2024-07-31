from django.test import TestCase, RequestFactory
from unittest.mock import Mock, patch
from fecfiler.devops.cf_api_utils import (
    get_space_guid,
    get_service_instance_guid,
    get_credentials_by_guid,
    merge_credentials,
    update_credentials_for_service,
    retrieve_credentials,
    update_credentials,
)


class CfApiUtilsTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    # retrieve_credentials

    @patch("fecfiler.devops.cf_api_utils.get_space_guid")
    def test_retrieve_credentials_throws_exception(
        self,
        get_space_guid_mock,
    ):
        test_token = "test_token"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        get_space_guid_mock.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "FAILED to retrieve credentials for space_name "
            f"{test_space_name} service_instance_name {test_service_instance_name}",
        ):
            retrieve_credentials(test_token, test_space_name, test_service_instance_name)

    @patch("fecfiler.devops.cf_api_utils.get_space_guid")
    @patch("fecfiler.devops.cf_api_utils.get_service_instance_guid")
    @patch("fecfiler.devops.cf_api_utils.get_credentials_by_guid")
    def test_retrieve_credentials_happy_path(
        self,
        get_credentials_by_guid_mock,
        get_service_instance_guid_mock,
        get_space_guid_mock,
    ):
        test_token = "test_token"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        mock_space_guid = "e04b544a-1fb5-4231-9934-eee244ebd2a2"
        mock_service_instance_guid = "6f80b064-2bb6-4c06-8af7-7e7ab02da970"
        mock_credentials = {"testkey1": "testval1"}

        get_space_guid_mock.return_value = mock_space_guid
        get_service_instance_guid_mock.return_value = mock_service_instance_guid
        get_credentials_by_guid_mock.return_value = mock_credentials

        actual_retval = retrieve_credentials(
            test_token, test_space_name, test_service_instance_name
        )
        self.assertEqual(actual_retval, mock_credentials)

    # update_credentials

    @patch("fecfiler.devops.cf_api_utils.get_space_guid")
    def test_update_credentials_throws_exception(
        self,
        get_space_guid_mock,
    ):
        test_token = "test_token"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"
        mock_credentials = {"testkey1": "testval1"}

        get_space_guid_mock.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "FAILED to update credentials for space_name "
            f"{test_space_name} service_instance_name {test_service_instance_name}",
        ):
            update_credentials(
                test_token, test_space_name, test_service_instance_name, mock_credentials
            )

    @patch("fecfiler.devops.cf_api_utils.get_space_guid")
    @patch("fecfiler.devops.cf_api_utils.get_service_instance_guid")
    @patch("fecfiler.devops.cf_api_utils.retrieve_credentials")
    @patch("fecfiler.devops.cf_api_utils.merge_credentials")
    @patch("fecfiler.devops.cf_api_utils.update_credentials_for_service")
    def test_update_credentials_happy_path(
        self,
        update_credentials_for_service_mock,
        merge_credentials_mock,
        retrieve_credentials_mock,
        get_service_instance_guid_mock,
        get_space_guid_mock,
    ):
        test_token = "test_token"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        mock_space_guid = "e04b544a-1fb5-4231-9934-eee244ebd2a2"
        mock_service_instance_guid = "6f80b064-2bb6-4c06-8af7-7e7ab02da970"
        mock_credentials = {"testkey1": "testval1"}

        get_space_guid_mock.return_value = mock_space_guid
        get_service_instance_guid_mock.return_value = mock_service_instance_guid
        retrieve_credentials_mock.return_value = mock_credentials
        merge_credentials_mock.return_value = mock_credentials

        update_credentials(
            test_token, test_space_name, test_service_instance_name, mock_credentials
        )
        self.assertEqual(True, True)

    # get_space_guid

    def test_get_space_guid_throws_exception(self):
        with patch("fecfiler.devops.cf_api_utils.requests") as mock_requests:
            test_token = "test_token"
            test_space_name = "test_space_name"
            mock_requests.get.side_effect = Exception("FAIL")
            with self.assertRaisesMessage(
                Exception, f"Failed to retrieve guid for space_name {test_space_name}"
            ):
                get_space_guid(test_token, test_space_name)

    def test_get_space_guid_empty_response(self):
        with patch("fecfiler.devops.cf_api_utils.requests") as mock_requests:
            test_token = "test_token"
            test_space_name = "test_space_name"
            test_guid = ""
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "resources": [{"name": test_space_name, "guid": test_guid}]
            }
            with self.assertRaisesMessage(
                Exception, f"Failed to retrieve guid for space_name {test_space_name}"
            ):
                get_space_guid(test_token, test_space_name)

    def test_get_space_guid_happy_path(self):
        with patch("fecfiler.devops.cf_api_utils.requests") as mock_requests:
            test_token = "test_token"
            test_space_name = "test_space_name"
            test_guid = "fd1ab0ac-691e-4755-9703-f6e0401e7b7a"
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "resources": [{"name": test_space_name, "guid": test_guid}]
            }
            response = get_space_guid(test_token, test_space_name)
            self.assertEqual(response, test_guid)

    # get_service_instance_guid

    def test_get_service_instance_guid_throws_exception(self):
        with patch("fecfiler.devops.cf_api_utils.requests") as mock_requests:
            test_token = "test_token"
            test_space_guid = "fd1ab0ac-691e-4755-9703-f6e0401e7b7a"
            test_service_instance_name = "test_service_instance_name"
            mock_requests.get.side_effect = Exception("FAIL")
            with self.assertRaisesMessage(
                Exception,
                "Failed to retrieve guid for service_instance_name "
                f"{test_service_instance_name} space_guid {test_space_guid}",
            ):
                get_service_instance_guid(
                    test_token, test_space_guid, test_service_instance_name
                )

    def test_get_service_instance_guid_empty_response(self):
        with patch("fecfiler.devops.cf_api_utils.requests") as mock_requests:
            test_token = "test_token"
            test_space_guid = "fd1ab0ac-691e-4755-9703-f6e0401e7b7a"
            test_service_instance_name = "test_service_instance_name"
            test_guid = ""
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "resources": [{"name": test_service_instance_name, "guid": test_guid}]
            }
            with self.assertRaisesMessage(
                Exception,
                "Failed to retrieve guid for service_instance_name "
                f"{test_service_instance_name} space_guid {test_space_guid}",
            ):
                get_service_instance_guid(
                    test_token, test_space_guid, test_service_instance_name
                )

    def test_get_service_instance_guid_happy_path(self):
        with patch("fecfiler.devops.cf_api_utils.requests") as mock_requests:
            test_token = "test_token"
            test_space_guid = "fd1ab0ac-691e-4755-9703-f6e0401e7b7a"
            test_service_instance_name = "test_service_instance_name"
            test_guid = "4430868a-a2b8-44a8-ae74-dea2e02d0225"
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "resources": [{"name": test_service_instance_name, "guid": test_guid}]
            }
            response = get_service_instance_guid(
                test_token, test_space_guid, test_service_instance_name
            )
            self.assertEqual(response, test_guid)

    # get_credentials_by_guid

    def test_get_credentials_by_guid_throws_exception(self):
        with patch("fecfiler.devops.cf_api_utils.requests") as mock_requests:
            test_token = "test_token"
            test_service_instance_guid = "1c694e15-9ba9-4b5c-8c52-8c4fc391c126"
            mock_requests.get.side_effect = Exception("FAIL")
            with self.assertRaisesMessage(
                Exception,
                "Failed to retrieve creds for service_instance_guid "
                f"{test_service_instance_guid}",
            ):
                get_credentials_by_guid(test_token, test_service_instance_guid)

    def test_get_credentials_by_guid_happy_path(self):
        with patch("fecfiler.devops.cf_api_utils.requests") as mock_requests:
            test_token = "test_token"
            test_service_instance_guid = "1c694e15-9ba9-4b5c-8c52-8c4fc391c126"
            test_creds = {"test_key1": "test_val1"}
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = test_creds
            response = get_credentials_by_guid(test_token, test_service_instance_guid)
            self.assertEqual(response, test_creds)

    # merge_credentials

    def test_merge_credentials_happy_path(self):
        test_creds = {"testkey1": "testval1"}
        test_update_data = {"testkey2": "testval2"}
        test_creds.update(test_update_data)
        expected_retval = {"credentials": test_creds}
        actual_retval = merge_credentials(test_creds, test_update_data)
        self.assertEqual(expected_retval, actual_retval)

    # update_credentials_for_service

    def test_update_credentials_for_service_throws_exception(self):
        with patch("fecfiler.devops.cf_api_utils.requests") as mock_requests:
            test_token = "test_token"
            test_service_instance_guid = "1c694e15-9ba9-4b5c-8c52-8c4fc391c126"
            test_creds = {"test_key1": "test_val1"}
            mock_requests.patch.side_effect = Exception("FAIL")
            with self.assertRaisesMessage(
                Exception,
                "Failed to patch creds for service_instance_guid "
                f"{test_service_instance_guid}",
            ):
                update_credentials_for_service(
                    test_token, test_service_instance_guid, test_creds
                )

    def test_update_credentials_for_service_happy_path(self):
        with patch("fecfiler.devops.cf_api_utils.requests") as mock_requests:
            test_token = "test_token"
            test_service_instance_guid = "1c694e15-9ba9-4b5c-8c52-8c4fc391c126"
            test_creds = {"test_key1": "test_val1"}
            mock_requests.patch.return_value = mock_response = Mock()
            mock_response.status_code = 200
            update_credentials_for_service(
                test_token, test_service_instance_guid, test_creds
            )
            self.assertEqual(True, True)

from django.test import TestCase
from unittest.mock import Mock, patch
from fecfiler.devops.utils.cf_api import (
    check_api_status,
    get_organization_guid,
    get_space_guid,
    get_service_instance_guid_from_names,
    get_service_instance_guid,
    get_credentials_by_guid,
    merge_credentials,
    update_credentials_for_service,
    retrieve_credentials,
    update_credentials,
)


class CfApiUtilsTestCase(TestCase):

    # check_api_status

    def test_check_api_status_error_response(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("FAIL")
            with self.assertRaisesMessage(
                Exception,
                "Failed to retrieve api status",
            ):
                check_api_status()

    def test_check_api_status_happy_path(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            response = check_api_status()
            self.assertEqual(response.status_code, 200)

    # retrieve_credentials

    @patch("fecfiler.devops.utils.cf_api.get_space_guid")
    def test_retrieve_credentials_throws_exception(
        self,
        get_space_guid_mock,
    ):
        test_token = "test_token"
        test_organization_name = "test_organization_name"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        get_space_guid_mock.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "FAILED to retrieve credentials for "
            f"organization_name {test_organization_name} "
            f"space_name {test_space_name} "
            f"service_instance_name {test_service_instance_name}",
        ):
            retrieve_credentials(
                test_token,
                test_organization_name,
                test_space_name,
                test_service_instance_name,
            )

    @patch("fecfiler.devops.utils.cf_api.get_space_guid")
    @patch("fecfiler.devops.utils.cf_api.get_service_instance_guid_from_names")
    @patch("fecfiler.devops.utils.cf_api.get_credentials_by_guid")
    def test_retrieve_credentials_happy_path(
        self,
        get_credentials_by_guid_mock,
        get_service_instance_guid_from_names_mock,
        get_space_guid_mock,
    ):
        test_token = "test_token"
        test_organization_name = "test_organization_name"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        mock_space_guid = "e04b544a-1fb5-4231-9934-eee244ebd2a2"
        mock_service_instance_guid = "6f80b064-2bb6-4c06-8af7-7e7ab02da970"
        mock_credentials = {"testkey1": "testval1"}

        get_space_guid_mock.return_value = mock_space_guid
        get_service_instance_guid_from_names_mock.return_value = (
            mock_service_instance_guid
        )
        get_credentials_by_guid_mock.return_value = mock_credentials

        actual_retval = retrieve_credentials(
            test_token,
            test_organization_name,
            test_space_name,
            test_service_instance_name,
        )
        self.assertEqual(actual_retval, mock_credentials)

    # update_credentials

    @patch("fecfiler.devops.utils.cf_api.get_space_guid")
    def test_update_credentials_throws_exception(
        self,
        get_space_guid_mock,
    ):
        test_token = "test_token"
        test_organization_name = "test_organization_name"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"
        mock_credentials = {"testkey1": "testval1"}

        get_space_guid_mock.side_effect = Exception("FAIL")

        with self.assertRaisesMessage(
            Exception,
            "FAILED to update credentials for "
            f"organization_name {test_organization_name} "
            f"space_name {test_space_name} "
            f"service_instance_name {test_service_instance_name}",
        ):
            update_credentials(
                test_token,
                test_organization_name,
                test_space_name,
                test_service_instance_name,
                mock_credentials,
            )

    @patch("fecfiler.devops.utils.cf_api.get_space_guid")
    @patch("fecfiler.devops.utils.cf_api.get_service_instance_guid_from_names")
    @patch("fecfiler.devops.utils.cf_api.get_credentials_by_guid")
    @patch("fecfiler.devops.utils.cf_api.merge_credentials")
    @patch("fecfiler.devops.utils.cf_api.update_credentials_for_service")
    def test_update_credentials_happy_path(
        self,
        update_credentials_for_service_mock,
        merge_credentials_mock,
        get_credentials_by_guid_mock,
        get_service_instance_guid_from_names_mock,
        get_space_guid_mock,
    ):
        test_token = "test_token"
        test_organization_name = "test_organization_name"
        test_space_name = "test_space_name"
        test_service_instance_name = "test_service_instance_name"

        mock_space_guid = "e04b544a-1fb5-4231-9934-eee244ebd2a2"
        mock_service_instance_guid = "6f80b064-2bb6-4c06-8af7-7e7ab02da970"
        mock_credentials = {"testkey1": "testval1"}

        get_space_guid_mock.return_value = mock_space_guid
        get_service_instance_guid_from_names_mock.return_value = (
            mock_service_instance_guid
        )
        get_credentials_by_guid_mock.return_value = mock_credentials
        merge_credentials_mock.return_value = mock_credentials

        update_credentials(
            test_token,
            test_organization_name,
            test_space_name,
            test_service_instance_name,
            mock_credentials,
        )
        self.assertEqual(True, True)

    # get_organization_guid

    def test_get_organization_guid_throws_exception(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            test_token = "test_token"
            test_organization_name = "test_organization_name"
            mock_requests.get.side_effect = Exception("FAIL")
            with self.assertRaisesMessage(
                Exception,
                f"Failed to retrieve guid for organization_name {test_organization_name}",
            ):
                get_organization_guid(test_token, test_organization_name)

    def test_get_organization_guid_empty_response(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            test_token = "test_token"
            test_organization_name = "test_organization_name"
            test_guid = ""
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "resources": [{"name": test_organization_name, "guid": test_guid}]
            }
            with self.assertRaisesMessage(
                Exception,
                f"Failed to retrieve guid for organization_name {test_organization_name}",
            ):
                get_organization_guid(test_token, test_organization_name)

    def test_get_organization_guid_happy_path(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            test_token = "test_token"
            test_organization_name = "test_organization_name"
            test_guid = "fd1ab0ac-691e-4755-9703-f6e0401e7b7a"
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "resources": [{"name": test_organization_name, "guid": test_guid}]
            }
            response = get_organization_guid(test_token, test_organization_name)
            self.assertEqual(response, test_guid)

    # get_space_guid

    def test_get_space_guid_throws_exception(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            test_token = "test_token"
            test_space_name = "test_space_name"
            test_organization_guid = "4baa2f2b-a5db-49fb-bbc3-330a7a5fada8"
            mock_requests.get.side_effect = Exception("FAIL")
            with self.assertRaisesMessage(
                Exception, f"Failed to retrieve guid for space_name {test_space_name}"
            ):
                get_space_guid(test_token, test_space_name, test_organization_guid)

    def test_get_space_guid_empty_response(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            test_token = "test_token"
            test_space_name = "test_space_name"
            test_organization_guid = "4baa2f2b-a5db-49fb-bbc3-330a7a5fada8"
            test_guid = ""
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "resources": [{"name": test_space_name, "guid": test_guid}]
            }
            with self.assertRaisesMessage(
                Exception, f"Failed to retrieve guid for space_name {test_space_name}"
            ):
                get_space_guid(test_token, test_space_name, test_organization_guid)

    def test_get_space_guid_happy_path(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            test_token = "test_token"
            test_space_name = "test_space_name"
            test_organization_guid = "4baa2f2b-a5db-49fb-bbc3-330a7a5fada8"
            test_guid = "fd1ab0ac-691e-4755-9703-f6e0401e7b7a"
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "resources": [{"name": test_space_name, "guid": test_guid}]
            }
            response = get_space_guid(test_token, test_space_name, test_organization_guid)
            self.assertEqual(response, test_guid)

    # get_service_instance_guid_from_names

    def test_get_service_instance_guid_from_names_throws_exception(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            test_token = "test_token"
            test_organization_name = "test_organization_name"
            test_space_name = "test_space_name"
            test_service_instance_name = "test_service_instance_name"
            mock_requests.get.side_effect = Exception("FAIL")
            with self.assertRaisesMessage(
                Exception,
                "Failed to retrieve service_instance_guid by names for "
                f"{test_organization_name} organization_name "
                f"{test_space_name} space_name "
                f"{test_service_instance_name} service_instance_name",
            ):
                get_service_instance_guid_from_names(
                    test_token,
                    test_organization_name,
                    test_space_name,
                    test_service_instance_name,
                )

    def test_get_service_instance_guid_from_names_happy_path(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            test_token = "test_token"
            test_organization_name = "test_organization_name"
            test_organization_guid = "c7773c33-e79d-483c-b90c-18ab6fa7b226"
            test_space_name = "test_space_name"
            test_space_guid = "9f820152-5633-4321-85dd-57e332771589"
            test_service_instance_name = "test_service_instance_name"
            test_service_instance_guid = "4430868a-a2b8-44a8-ae74-dea2e02d0225"

            get_organization_guid_mock_response = Mock()
            get_organization_guid_mock_response.status_code = 200
            get_organization_guid_mock_response.json.return_value = {
                "resources": [
                    {
                        "name": test_organization_name,
                        "guid": test_organization_guid,
                    }
                ]
            }

            get_space_guid_mock_response = Mock()
            get_space_guid_mock_response.status_code = 200
            get_space_guid_mock_response.json.return_value = {
                "resources": [{"name": test_space_name, "guid": test_space_guid}]
            }

            get_service_instance_guid_mock_response = Mock()
            get_service_instance_guid_mock_response.status_code = 200
            get_service_instance_guid_mock_response.json.return_value = {
                "resources": [
                    {
                        "name": test_service_instance_name,
                        "guid": test_service_instance_guid,
                    }
                ]
            }

            mock_requests.get.side_effect = [
                get_organization_guid_mock_response,
                get_space_guid_mock_response,
                get_service_instance_guid_mock_response,
            ]
            response = get_service_instance_guid_from_names(
                test_token,
                test_organization_name,
                test_space_name,
                test_service_instance_name,
            )
            self.assertEqual(response, test_service_instance_guid)

    # get_service_instance_guid

    def test_get_service_instance_guid_throws_exception(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            test_token = "test_token"
            test_organization_guid = "7b9734d0-caf0-4c03-9b0c-063c0a9e0c30"
            test_space_guid = "fd1ab0ac-691e-4755-9703-f6e0401e7b7a"
            test_service_instance_name = "test_service_instance_name"
            mock_requests.get.side_effect = Exception("FAIL")
            with self.assertRaisesMessage(
                Exception,
                "Failed to retrieve service_instance_guid by guids for "
                f"{test_organization_guid} organization_guid "
                f"{test_space_guid} space_guid "
                f"{test_service_instance_name} service_instance_name",
            ):
                get_service_instance_guid(
                    test_token,
                    test_organization_guid,
                    test_space_guid,
                    test_service_instance_name,
                )

    def test_get_service_instance_guid_empty_response(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            test_token = "test_token"
            test_organization_guid = "7b9734d0-caf0-4c03-9b0c-063c0a9e0c30"
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
                "Failed to retrieve service_instance_guid by guids for "
                f"{test_organization_guid} organization_guid "
                f"{test_space_guid} space_guid "
                f"{test_service_instance_name} service_instance_name",
            ):
                get_service_instance_guid(
                    test_token,
                    test_organization_guid,
                    test_space_guid,
                    test_service_instance_name,
                )

    def test_get_service_instance_guid_happy_path(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            test_token = "test_token"
            test_organization_guid = "7b9734d0-caf0-4c03-9b0c-063c0a9e0c30"
            test_space_guid = "fd1ab0ac-691e-4755-9703-f6e0401e7b7a"
            test_service_instance_name = "test_service_instance_name"
            test_guid = "4430868a-a2b8-44a8-ae74-dea2e02d0225"
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "resources": [{"name": test_service_instance_name, "guid": test_guid}]
            }
            response = get_service_instance_guid(
                test_token,
                test_organization_guid,
                test_space_guid,
                test_service_instance_name,
            )
            self.assertEqual(response, test_guid)

    # get_credentials_by_guid

    def test_get_credentials_by_guid_throws_exception(self):
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
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
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
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
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
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
        with patch("fecfiler.devops.utils.cf_api.requests") as mock_requests:
            test_token = "test_token"
            test_service_instance_guid = "1c694e15-9ba9-4b5c-8c52-8c4fc391c126"
            test_creds = {"test_key1": "test_val1"}
            mock_requests.patch.return_value = mock_response = Mock()
            mock_response.status_code = 200
            update_credentials_for_service(
                test_token, test_service_instance_guid, test_creds
            )
            self.assertEqual(True, True)

# from django.test import TestCase
# from fecfiler.authentication.models import Account
# from rest_framework.request import HttpRequest, Request

# from fecfiler.transactions.schedule_c1.serializers import (
#     ScheduleC1TransactionSerializer,
# )


# class ScheduleC1TransactionSerializerTestCase(TestCase):
#     def setUp(self):
#         self.new_contact = {
#             "id": "9bb5c8b2-31f3-488f-84e1-a63b0133a000",
#             "type": "ORG",
#             "name": "Bank",
#             "street_1": "Street",
#             "city": "City",
#             "state": "CA",
#             "zip": "12345678",
#             "country": "Country",
#             "created": "2022-02-09T00:00:00.000Z",
#             "updated": "2022-02-09T00:00:00.000Z",
#             "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
#         }
#         self.valid_schedule_c1_transaction = {
#             "form_type": "SC1/9",
#             "transaction_type_identifier": "SCHEDULE_C1",
#             "transaction_id": "ABCDEF0123456789",
#             "back_reference_tran_id_number": "BBCDEF0123456789",
#             "lender_organization_name": "Big Bank",
#             "lender_state": "AK",
#             "lender_city": "Homer",
#             "lender_zip": "1234",
#             "lender_street_1": "1 Homer Spit Road",
#             "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
#             "contact": self.new_contact,
#             "schema_name": "SchC1",
#             "loan_amount": "1000.00",
#             "loan_incurred_date": "2022-10-05",
#             "loan_due_date": "2023-11-09",
#             "treasurer_last_name": "Tlastname",
#             "treasurer_first_name": "Tfirstname",
#             "treasurer_date_signed": "2023-12-03",
#             "authorized_last_name": "Alastname",
#             "authorized_first_name": "Afirstname",
#             "authorized_title": "Atitle",
#             "authorized_date_signed": "2023-08-17",
#         }

#         self.mock_request = Request(HttpRequest())
#         user = Account()
#         user.cmtee_id = "C00277616"
#         self.mock_request.user = user

#     def test_serializer_validate(self):
#         valid_serializer = ScheduleC1TransactionSerializer(
#             data=self.valid_schedule_c1_transaction,
#             context={"request": self.mock_request},
#         )
#         self.assertTrue(valid_serializer.is_valid(raise_exception=True))
#         invalid_transaction = self.valid_schedule_c1_transaction.copy()
#         invalid_transaction["form_type"] = "invalidformtype"
#         del invalid_transaction["lender_organization_name"]
#         invalid_serializer = ScheduleC1TransactionSerializer(
#             data=invalid_transaction, context={"request": self.mock_request},
#         )
#         self.assertFalse(invalid_serializer.is_valid())
#         self.assertIsNotNone(invalid_serializer.errors["form_type"])
#         self.assertIsNotNone(invalid_serializer.errors["lender_organization_name"])

#     def test_no_lender_organization_name(self):
#         missing_type = self.valid_schedule_c1_transaction.copy()
#         del missing_type["lender_organization_name"]
#         missing_type_serializer = ScheduleC1TransactionSerializer(
#             data=missing_type, context={"request": self.mock_request},
#         )
#         self.assertFalse(missing_type_serializer.is_valid())
#         self.assertIsNotNone(missing_type_serializer.errors["lender_organization_name"])

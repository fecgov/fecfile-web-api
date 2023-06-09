from django.test import TestCase

from fecfiler.contacts.models import Contact
from fecfiler.transactions.schedule_c2.models import ScheduleC2


class ScheduleC2TransactionModelTestCase(TestCase):
    def setUp(self):
        self.new_contact = Contact()
        self.new_contact.id = "9bb5c8b2-31f3-488f-84e1-a63b0133a000"
        self.new_contact.type = "IND"
        self.new_contact.last_name = "Smith"
        self.new_contact.first_name = "John"
        self.new_contact.street_1 = "Street"
        self.new_contact.city = "City"
        self.new_contact.state = "CA"
        self.new_contact.zip = "12345678"
        self.new_contact.country = "Country"
        self.new_contact.created = "2022-02-09T00:00:00.000Z"
        self.new_contact.updated = "2022-02-09T00:00:00.000Z"
        self.new_contact.committee_account_id = "735db943-9446-462a-9be0-c820baadb622"

    def test_model_contact_assignment(self):
        sched_c2 = ScheduleC2()
        sched_c2.update_with_contact(self.new_contact)
        self.assertEquals(sched_c2.guarantor_last_name, "Smith")
        self.assertEquals(sched_c2.guarantor_zip, "12345678")

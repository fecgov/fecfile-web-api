from django.test import TestCase
from .utilities import generate_fec_uid


class SharedUtilitiesTestCase(TestCase):
    def test_uid_has_length_20(self):
        uid = generate_fec_uid()
        self.assertEquals(len(uid), 20)

    def test_uid_all_uppercase(self):
        uid = generate_fec_uid()
        upper = uid.upper()
        self.assertEquals(uid, upper)

from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import F3X


class F3XTestCase(TestCase):
    """ Test module for inserting an f3x item"""
    fixtures = ['test_f3xs']

    def test_get_f3x(self):
        f3x = F3X.objects.get(treasurer_last_name="Dobalina")
        self.assertEquals(f3x.form_type, "F3XN")

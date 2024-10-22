from decimal import Decimal
from django.test import TestCase
from .models import F3xLine6aOverride


class F3xLine6aOverrideTestCase(TestCase):
    fixtures = ["test_f3x_line6a_overrides"]

    def test_f3x_line6a_override_crud(self):
        self.test_f3x_line6a_override = F3xLine6aOverride(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4",
            year="2024",
            cash_on_hand=501.40,
        )
        self.test_f3x_line6a_override.save()

        override_2024 = F3xLine6aOverride.objects.get(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4"
        )
        self.assertEquals(override_2024.year, "2024")
        self.assertEquals(override_2024.cash_on_hand, Decimal("501.40"))

        F3xLine6aOverride.objects.filter(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4"
        ).update(cash_on_hand=300.00)
        override_2024 = F3xLine6aOverride.objects.get(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4"
        )
        self.assertEquals(override_2024.cash_on_hand, 300.00)

        F3xLine6aOverride.objects.filter(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4"
        ).delete()

        with self.assertRaises(F3xLine6aOverride.DoesNotExist):
            override_2024 = F3xLine6aOverride.objects.get(
                id="422095b3-e0a7-4499-9d2c-5efb3858fce4",
            )

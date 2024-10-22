from decimal import Decimal
from django.test import TestCase
from .models import F3xLine6aOverride


class F3xLine6aOverrideTestCase(TestCase):
    fixtures = ["test_f3x_line6a_overrides"]

    def test_f3x_line6a_override_crud(self):
        self.test_f3x_line6a_override = F3xLine6aOverride(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4",
            L6a_cash_on_hand_jan_1_ytd=501.40,
            L6a_year_for_above_ytd="2024",
        )
        self.test_f3x_line6a_override.save()

        override_2024 = F3xLine6aOverride.objects.get(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4"
        )
        self.assertEquals(override_2024.L6a_cash_on_hand_jan_1_ytd, Decimal("501.40"))
        self.assertEquals(override_2024.L6a_year_for_above_ytd, "2024")

        F3xLine6aOverride.objects.filter(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4"
        ).update(L6a_cash_on_hand_jan_1_ytd=300.00)
        override_2024 = F3xLine6aOverride.objects.get(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4"
        )
        self.assertEquals(override_2024.L6a_cash_on_hand_jan_1_ytd, 300.00)

        F3xLine6aOverride.objects.filter(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4"
        ).delete()

        with self.assertRaises(F3xLine6aOverride.DoesNotExist):
            override_2024 = F3xLine6aOverride.objects.get(
                id="422095b3-e0a7-4499-9d2c-5efb3858fce4",
            )

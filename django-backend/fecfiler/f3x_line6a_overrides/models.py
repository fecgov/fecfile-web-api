from django.db import models
import uuid


class F3xLine6aOverride(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    year = models.TextField(null=False, blank=False, unique=True)
    cash_on_hand = models.DecimalField(
        null=False, blank=False, max_digits=11, decimal_places=2
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "f3x_line6a_overrides"

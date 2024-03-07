from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from fecfiler.user.managers import UserManager


class User(AbstractUser):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    first_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    groups = None
    user_permissions = None
    security_consent_date = models.DateField(null=True, blank=True)

    objects = UserManager()

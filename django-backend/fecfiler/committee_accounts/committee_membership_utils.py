import requests
import re
from rest_framework.exceptions import ValidationError
from .models import CommitteeAccount, Membership

from fecfiler import settings
import redis
import json
import structlog

logger = structlog.getLogger(__name__)

def add_user_to_committee(email, role, committee):

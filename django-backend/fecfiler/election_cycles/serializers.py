from .models import ElectionCycle
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from rest_framework.serializers import BooleanField
import structlog

logger = structlog.getLogger(__name__)


class ElectionCycleSerializer(CommitteeOwnedSerializer):
    has_form3 = BooleanField(read_only=True)

    class Meta:
        model = ElectionCycle
        fields = [
            "id",
            "committee_account",
            "office",
            "election_type",
            "election_year",
            "start_date",
            "end_date",
            "has_form3",
        ]
        read_only_fields = ["id", "committee_account"]

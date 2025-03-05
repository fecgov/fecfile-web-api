from .models import CashOnHandYearly
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
import structlog

logger = structlog.getLogger(__name__)


class CashOnHandYearlySerializer(CommitteeOwnedSerializer):
    class Meta:
        model = CashOnHandYearly
        fields = [f.name for f in CashOnHandYearly._meta.get_fields()]
        read_only_fields = [
            "id",
            "created",
            "updated",
        ]

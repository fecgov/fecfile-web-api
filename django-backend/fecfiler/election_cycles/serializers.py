from .models import ElectionCycle
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
import structlog

logger = structlog.getLogger(__name__)


class ElectionCycleSerializer(CommitteeOwnedSerializer):
    class Meta:
        model = ElectionCycle
        fields = [f.name for f in ElectionCycle._meta.get_fields()]
        read_only_fields = ["id"]

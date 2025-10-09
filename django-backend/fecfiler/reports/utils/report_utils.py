from ..models import Report
from uuid import UUID
import structlog

logger = structlog.get_logger(__name__)


def reset_summary_calculation_state(id):
    report_uuid = UUID(id)
    Report.objects.filter(id=report_uuid).update(calculation_status=None)

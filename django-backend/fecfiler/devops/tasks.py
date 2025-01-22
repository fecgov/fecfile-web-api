from django.db import connection
from celery import shared_task
import structlog

logger = structlog.get_logger(__name__)


@shared_task
def get_database_connections():

    column_labels = (
        "total_connections",
        "non_idle_connections",
        "max_connections",
        "connections_utilization_pctg",
    )

    sql = """
        SELECT
        A.total_connections::text AS {},
        A.non_idle_connections::text AS {},
        B.max_connections::text AS {},
        ROUND(
            100 * (A.total_connections::numeric / B.max_connections::numeric), 2)::text
            AS {}
        FROM
        (SELECT count(1) AS total_connections,
         SUM(CASE WHEN state!='idle' THEN 1 ELSE 0 END) AS non_idle_connections
         FROM pg_stat_activity) A,
        (SELECT setting AS max_connections FROM pg_settings
         WHERE name='max_connections') B;
        """.format(
        *column_labels
    )

    with connection.cursor() as cursor:
        cursor.execute(sql)
        results = cursor.fetchall()

    results_dict = {"results": dict(zip(column_labels, row)) for row in results}
    logger.info(results_dict)

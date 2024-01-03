import json
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Prints database connection stats"

    COLUMN_LABELS = (
        'total_connections',
        'non_idle_connections',
        'max_connections',
        'connections_utilization_pctg',
    )

    SQL = """
        SELECT
        A.total_connections AS {},
        A.non_idle_connections AS {},
        B.max_connections AS {},
        ROUND(
            (100 * A.total_connections::numeric / B.max_connections::numeric), 0
            )::INTEGER
            AS {}
        FROM
        (SELECT count(1) AS total_connections,
         SUM(CASE WHEN state!='idle' THEN 1 ELSE 0 END) AS non_idle_connections
         FROM pg_stat_activity) A,
        (SELECT setting AS max_connections FROM pg_settings
         WHERE name='max_connections') B;
        """.format(*COLUMN_LABELS)

    def get_pg_stat_activity(self):

        with connection.cursor() as cursor:
            cursor.execute(self.SQL)
            results = cursor.fetchall()

        return results

    def handle(self, *args, **options):

        pg_stat_activity_data = self.get_pg_stat_activity()
        keys = self.COLUMN_LABELS
        results = [dict(zip(keys, row)) for row in pg_stat_activity_data]
        json_data = json.dumps(results)
        print(json_data)

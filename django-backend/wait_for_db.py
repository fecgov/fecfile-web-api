import psycopg2
import os
from retrying import retry


@retry
def postgres_test():
    try:
        conn = psycopg2.connect(
            'dbname={} user={} host={} password={} connect_timeout=3000'.
            format(
                os.environ.get('DB_NAME'),
                os.environ.get('DB_USERNAME'),
                os.environ.get('DB_HOST'),
                os.environ.get('DB_PASSWORD')))
        conn.close()
        return True
    except ImportError:
        return False


postgres_test()

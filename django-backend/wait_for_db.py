import psycopg2
import os
from retrying import retry


@retry(wait_fixed=2000)
def postgres_test():
    try:

        print("testing connection with dbname={} user={} host={} password={} connect_timeout=3000".
            format(
            os.environ.get('FECFILE_DB_NAME'),
            os.environ.get('FECFILE_DB_USERNAME'),
            os.environ.get('FECFILE_DB_HOST'),
            os.environ.get('FECFILE_DB_PASSWORD')))

        conn = psycopg2.connect(
            'dbname={} user={} host={} password={} connect_timeout=3000'.
            format(
                os.environ.get('FECFILE_DB_NAME'),
                os.environ.get('FECFILE_DB_USERNAME'),
                os.environ.get('FECFILE_DB_HOST'),
                os.environ.get('FECFILE_DB_PASSWORD')))
        conn.close()
        return True
    except ImportError:
        return False


postgres_test()

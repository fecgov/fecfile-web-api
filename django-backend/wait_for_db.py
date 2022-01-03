import psycopg2
import os
from retry import retry


@retry(delay=2, tries=15)
def postgres_test():
    try:

        if os.environ.get('FECFILE_DB_NAME') == None and os.environ.get('FECFILE_DB_PASSWORD') == None:
            print("Environment settings for database and password not found. Please check your settings and try again")
            exit(1)

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
        print("DB connection successful")
        return True
    except ImportError:
        return False


postgres_test()

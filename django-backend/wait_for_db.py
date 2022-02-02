import psycopg2
import os
from retry import retry


@retry(delay=2, tries=15)
def postgres_test():
    try:
        database_uri = os.environ.get('DATABASE_URL')
        if not database_uri:
            print("Environment variable DATABASE_URL not found. Please check your settings and try again")
            exit(1)
        print("Testing connection...")
        conn = psycopg2.connect(database_uri)
        conn.close()
        print("DB connection successful")
        return True
    except ImportError:
        return False


postgres_test()
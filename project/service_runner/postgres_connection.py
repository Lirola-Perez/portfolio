import os
from decorator import contextmanager
import psycopg2

# Reading the .env injected by Docker Compose
@contextmanager
def get_db_connection():
    '''Opens and returns a PostgreSQL connection'''
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres-db"),
        database=os.getenv("DATABASE_NAME"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return conn
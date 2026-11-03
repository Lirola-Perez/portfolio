import os

import psycopg2
from decorator import contextmanager


# Reading the .env injected by Docker Compose
@contextmanager
def get_db_connection(database_connect="None"):
    # 1. Choose whether to use an explicit connection string or individual env vars
    if database_connect and database_connect != "value":
        conn = psycopg2.connect(database_connect)
    else:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres-db"),
            database=os.getenv("DATABASE_NAME"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            port=os.getenv("DB_PORT", "5432")
        )
    # Execution
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return conn
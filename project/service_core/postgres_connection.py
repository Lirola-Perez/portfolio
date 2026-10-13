import os
import psycopg2

# Reading the .env injected by Docker Compose

DB_USER=os.getenv("DATABASE_USER")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD")
DB_NAME = os.getenv("DATABASE_NAME")
DB_HOST = os.getenv("DB_HOST", "postgres-db")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    '''Opens and returns a PostgreSQL connection'''
    connection = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password_db=DB_PASSWORD,
        port=DB_PORT
    )
    return connection
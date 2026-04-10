"""
Shared database connection pool for the unified platform.

All modules use this pool to access the shared PostgreSQL database.
"""

from psycopg2.pool import SimpleConnectionPool

from config import DATABASE_URL

pool = SimpleConnectionPool(1, 10, DATABASE_URL)


def get_conn():
    return pool.getconn()


def put_conn(conn):
    pool.putconn(conn)

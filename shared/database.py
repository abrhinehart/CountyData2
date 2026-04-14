"""
Shared database connection pool for the unified platform.

All modules use this pool to access the shared PostgreSQL database.

The pool is lazily initialized: the underlying psycopg2 SimpleConnectionPool
is not created until the first call that actually needs a connection
(e.g. ``getconn``). This lets the module be imported in environments where
Postgres is not reachable (tests, tooling, etc.) without raising at import
time. The ``pool`` module attribute is a ``_LazyPool`` proxy that forwards
all attribute access to the real pool once it has been constructed.
"""

from psycopg2.pool import SimpleConnectionPool

from config import DATABASE_URL


class _LazyPool:
    def __init__(self, minconn, maxconn, dsn):
        self._args = (minconn, maxconn, dsn)
        self._pool = None

    def _ensure(self):
        if self._pool is None:
            self._pool = SimpleConnectionPool(*self._args)
        return self._pool

    def getconn(self, *a, **kw):
        return self._ensure().getconn(*a, **kw)

    def putconn(self, *a, **kw):
        return self._ensure().putconn(*a, **kw)

    def closeall(self):
        if self._pool is not None:
            self._pool.closeall()

    def __getattr__(self, name):  # delegate anything else to the real pool
        return getattr(self._ensure(), name)


pool = _LazyPool(1, 10, DATABASE_URL)


def get_conn():
    return pool.getconn()


def put_conn(conn):
    pool.putconn(conn)

"""PostgreSQL connection pool.

DATABASE_URL in .env turns the database on. Without it the API stays in mock mode
and nothing here connects, so designers can run the API with no database installed.
"""
import atexit
import os
from typing import Iterator, Optional

import psycopg
from fastapi import HTTPException
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout

UNREACHABLE = (
    "The database is not reachable. Check that PostgreSQL is running "
    "and that DATABASE_URL in .env is correct."
)

_pool: Optional[ConnectionPool] = None
_pool_url: Optional[str] = None


def enabled() -> bool:
    return bool(os.getenv("DATABASE_URL", "").strip())


def get_pool() -> ConnectionPool:
    """Open the pool on first use. Reopens it if DATABASE_URL has changed."""
    global _pool, _pool_url
    url = os.environ["DATABASE_URL"].strip()
    if _pool is not None and _pool_url != url:
        close_pool()
    if _pool is None:
        pool = ConnectionPool(url, min_size=1, max_size=5, kwargs={"row_factory": dict_row}, open=False)
        try:
            pool.open(wait=True, timeout=3)
        except Exception:
            pool.close()
            raise
        _pool, _pool_url = pool, url
    return _pool


def close_pool() -> None:
    global _pool, _pool_url
    if _pool is not None:
        _pool.close()
    _pool = None
    _pool_url = None


atexit.register(close_pool)


def get_conn() -> Iterator[Optional[psycopg.Connection]]:
    """FastAPI dependency. Gives a connection, or None in mock mode.

    Routes that write must call conn.commit() themselves.
    """
    if not enabled():
        yield None
        return
    try:
        pool = get_pool()
    except (psycopg.OperationalError, PoolTimeout) as exc:
        raise HTTPException(503, UNREACHABLE) from exc
    with pool.connection() as conn:
        yield conn

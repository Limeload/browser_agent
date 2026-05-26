"""
PostgreSQL async client — Week 4.

Provides best-effort logging of injection detections to injection_events table.
If the database is unavailable (no DATABASE_URL, asyncpg not installed, or
connection failure), operations degrade silently so the agent keeps running.
"""

import logging
import os

logger = logging.getLogger(__name__)

_pool = None  # None = not yet attempted; False = attempted but unavailable

_DEFAULT_DSN = "postgresql://guardagent:guardagent@localhost:5432/guardagent"


async def _get_pool():
    global _pool
    if _pool is not None:
        return _pool if _pool is not False else None
    dsn = os.environ.get("DATABASE_URL", _DEFAULT_DSN)
    try:
        import asyncpg  # type: ignore

        _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5, command_timeout=5)
        await _create_schema(_pool)
        logger.info("PostgreSQL connected: %s", dsn.split("@")[-1])
    except Exception as exc:
        logger.info("PostgreSQL unavailable (%s) — detections will not be persisted", exc)
        _pool = False
    return _pool if _pool is not False else None


async def _create_schema(pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS injection_events (
                id           SERIAL PRIMARY KEY,
                detected_at  TIMESTAMPTZ DEFAULT NOW(),
                attack_type  TEXT NOT NULL,
                confidence   REAL NOT NULL,
                source       TEXT NOT NULL,
                matched_text TEXT,
                page_url     TEXT,
                raw_text     TEXT
            )
            """
        )


async def log_detection(
    attack_type: str,
    confidence: float,
    source: str,
    matched_text: str,
    page_url: str = "",
    raw_text: str = "",
) -> None:
    pool = await _get_pool()
    if pool is None:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO injection_events
                    (attack_type, confidence, source, matched_text, page_url, raw_text)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                attack_type,
                confidence,
                source,
                matched_text,
                page_url,
                raw_text[:2_000],
            )
    except Exception as exc:
        logger.warning("Failed to persist detection: %s", exc)


async def close() -> None:
    global _pool
    if _pool and _pool is not False:
        await _pool.close()
        _pool = None

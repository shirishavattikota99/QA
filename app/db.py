"""Chat history (question + answer) stored with SQL.

Two backends, chosen automatically:
  * DATABASE_URL set  -> PostgreSQL (hosted, e.g. Neon/Supabase). Best for production.
  * DATABASE_URL unset -> SQLite file (chat_history.db). Built into Python: no install,
                          no account, works immediately. Best for local development.

Saving never breaks the chat: any database error is logged and ignored.
"""
import json
import os
import sqlite3
from pathlib import Path
from typing import Optional

from app.helpers.logger import logger

_backend: Optional[str] = None   # "postgres" | "sqlite" | None (disabled)
_pool = None                     # PostgreSQL connection pool
_sqlite_path: Optional[str] = None

COLUMNS = (
    "id", "created_at", "question", "answer", "success", "error",
    "generated_query", "row_count", "duration_ms", "route", "sources",
)

# ---------------------------------------------------------------------------
# PostgreSQL schema
# ---------------------------------------------------------------------------
PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_history (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    partner_id      TEXT        NOT NULL,
    app_client      TEXT,
    node_env        TEXT,
    question        TEXT        NOT NULL,
    answer          TEXT,
    success         BOOLEAN     NOT NULL,
    error           TEXT,
    generated_query TEXT,
    row_count       INTEGER,
    duration_ms     INTEGER,
    route           TEXT,
    sources         TEXT[]
);
-- for tables created before route/sources existed
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS route TEXT;
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS sources TEXT[];
<<<<<<< HEAD
-- conversation continuity: turns of one chat share a conversation_id
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS conversation_id TEXT;
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS resolved_question TEXT;
CREATE INDEX IF NOT EXISTS idx_chat_history_partner_created
    ON chat_history (partner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_history_conversation
    ON chat_history (partner_id, conversation_id, created_at);
=======
CREATE INDEX IF NOT EXISTS idx_chat_history_partner_created
    ON chat_history (partner_id, created_at DESC);
>>>>>>> origin/main
"""

# ---------------------------------------------------------------------------
# SQLite schema (same columns; sources is stored as JSON text)
# ---------------------------------------------------------------------------
SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    partner_id      TEXT    NOT NULL,
    app_client      TEXT,
    node_env        TEXT,
    question        TEXT    NOT NULL,
    answer          TEXT,
    success         INTEGER NOT NULL,
    error           TEXT,
    generated_query TEXT,
    row_count       INTEGER,
    duration_ms     INTEGER,
    route           TEXT,
<<<<<<< HEAD
    sources         TEXT,
    conversation_id   TEXT,
    resolved_question TEXT
=======
    sources         TEXT
>>>>>>> origin/main
);
CREATE INDEX IF NOT EXISTS idx_chat_history_partner_created
    ON chat_history (partner_id, created_at DESC);
"""

<<<<<<< HEAD
# Columns added after the first release. SQLite has no "ADD COLUMN IF NOT EXISTS",
# so init_db adds whichever of these an older chat_history.db file is missing.
SQLITE_NEW_COLUMNS = {"conversation_id": "TEXT", "resolved_question": "TEXT"}
SQLITE_CONVERSATION_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_chat_history_conversation "
    "ON chat_history (partner_id, conversation_id, created_at)"
)

=======
>>>>>>> origin/main

def _sqlite_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_sqlite_path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> bool:
    """Pick a backend and create the table. Returns True if history is enabled."""
    global _backend, _pool, _sqlite_path
    url = os.getenv("DATABASE_URL")

    if url:
        try:
            from psycopg_pool import ConnectionPool  # imported only when PostgreSQL is used

            _pool = ConnectionPool(
                url,
                min_size=1,
                max_size=5,
                open=False,
                timeout=30,
                # drop connections the server closed while idle (free tiers suspend)
                check=ConnectionPool.check_connection,
                # prepare_threshold=None keeps it working through pooled (pgbouncer) endpoints
                kwargs={"autocommit": True, "prepare_threshold": None},
            )
            _pool.open(wait=True, timeout=20)  # first connect can take seconds if the DB was asleep
            with _pool.connection() as conn:
                conn.execute(PG_SCHEMA)
            _backend = "postgres"
            logger.info("Chat history enabled (PostgreSQL)")
            return True
        except Exception as e:
            logger.error("Could not connect to PostgreSQL, history disabled: %s", e)
            if _pool is not None:
                _pool.close()  # stop the background reconnect attempts
            _pool, _backend = None, None
            return False

    # No DATABASE_URL: use a local SQLite file
    try:
        default = Path(__file__).resolve().parents[1] / "chat_history.db"  # project root
        _sqlite_path = os.getenv("SQLITE_PATH", str(default))
        with _sqlite_connect() as conn:
            conn.executescript(SQLITE_SCHEMA)
<<<<<<< HEAD
            existing = {row["name"] for row in conn.execute("PRAGMA table_info(chat_history)")}
            for column, ctype in SQLITE_NEW_COLUMNS.items():
                if column not in existing:
                    conn.execute(f"ALTER TABLE chat_history ADD COLUMN {column} {ctype}")
            conn.execute(SQLITE_CONVERSATION_INDEX)
=======
>>>>>>> origin/main
        _backend = "sqlite"
        logger.info("Chat history enabled (SQLite file: %s)", _sqlite_path)
        return True
    except Exception as e:
        logger.error("Could not open SQLite file, history disabled: %s", e)
        _backend = None
        return False


def close_db() -> None:
    global _backend
    if _pool is not None:
        _pool.close()
    _backend = None


def save_chat(
    *,
    partner_id: str,
    question: str,
    answer: Optional[str],
    success: bool,
    app_client: Optional[str] = None,
    node_env: Optional[str] = None,
    error: Optional[str] = None,
    generated_query: Optional[str] = None,
    row_count: Optional[int] = None,
    duration_ms: Optional[int] = None,
    route: Optional[str] = None,
    sources: Optional[list] = None,
<<<<<<< HEAD
    conversation_id: Optional[str] = None,
    resolved_question: Optional[str] = None,
=======
>>>>>>> origin/main
) -> None:
    """Insert one question/answer. Never raises: saving must not break the chat."""
    if _backend is None:
        return
    error = error[:1000] if error else None
    try:
        if _backend == "postgres":
            with _pool.connection() as conn:
                conn.execute(
                    """
                    INSERT INTO chat_history
                        (partner_id, app_client, node_env, question, answer, success,
<<<<<<< HEAD
                         error, generated_query, row_count, duration_ms, route, sources,
                         conversation_id, resolved_question)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (partner_id, app_client, node_env, question, answer, success,
                     error, generated_query, row_count, duration_ms, route, sources or None,
                     conversation_id, resolved_question),
=======
                         error, generated_query, row_count, duration_ms, route, sources)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (partner_id, app_client, node_env, question, answer, success,
                     error, generated_query, row_count, duration_ms, route, sources or None),
>>>>>>> origin/main
                )
        else:
            with _sqlite_connect() as conn:
                conn.execute(
                    """
                    INSERT INTO chat_history
                        (partner_id, app_client, node_env, question, answer, success,
<<<<<<< HEAD
                         error, generated_query, row_count, duration_ms, route, sources,
                         conversation_id, resolved_question)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (partner_id, app_client, node_env, question, answer, int(success),
                     error, generated_query, row_count, duration_ms, route,
                     json.dumps(sources) if sources else None,
                     conversation_id, resolved_question),
=======
                         error, generated_query, row_count, duration_ms, route, sources)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (partner_id, app_client, node_env, question, answer, int(success),
                     error, generated_query, row_count, duration_ms, route,
                     json.dumps(sources) if sources else None),
>>>>>>> origin/main
                )
    except Exception as e:
        logger.error("Could not save chat history: %s", e)


def get_history(partner_id: str, limit: int = 50) -> list[dict]:
    if _backend is None:
        return []
    limit = max(1, min(limit, 100))
    cols = ", ".join(COLUMNS)

    if _backend == "postgres":
        from psycopg.rows import dict_row

        with _pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"SELECT {cols} FROM chat_history WHERE partner_id = %s "
                    "ORDER BY created_at DESC LIMIT %s",
                    (partner_id, limit),
                )
                return cur.fetchall()

    with _sqlite_connect() as conn:
        rows = conn.execute(
            f"SELECT {cols} FROM chat_history WHERE partner_id = ? "
            "ORDER BY created_at DESC, id DESC LIMIT ?",
            (partner_id, limit),
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["success"] = bool(d["success"])
        d["sources"] = json.loads(d["sources"]) if d["sources"] else None
        result.append(d)
<<<<<<< HEAD
    return result

# ---------------------------------------------------------------------------
# Conversations: turns of one chat share a conversation_id
# ---------------------------------------------------------------------------
def _fetch(sql: str, params: tuple) -> list[dict]:
    """Run a SELECT on either backend. `sql` uses %s placeholders (SQLite gets ?)."""
    if _backend == "postgres":
        from psycopg.rows import dict_row

        with _pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchall()
    with _sqlite_connect() as conn:
        return [dict(r) for r in conn.execute(sql.replace("%s", "?"), params).fetchall()]


def _clean_row(row: dict) -> dict:
    row = dict(row)
    if "success" in row:
        row["success"] = bool(row["success"])
    if isinstance(row.get("sources"), str):
        row["sources"] = json.loads(row["sources"])
    return row


def get_conversation(partner_id: str, conversation_id: str, limit: int = 100) -> list[dict]:
    """All turns of one conversation, oldest first (for showing a saved chat)."""
    if _backend is None or not conversation_id:
        return []
    limit = max(1, min(limit, 200))
    cols = ", ".join(c for c in COLUMNS if c != "id") + ", resolved_question"
    rows = _fetch(
        f"SELECT {cols} FROM chat_history WHERE partner_id = %s AND conversation_id = %s "
        "ORDER BY created_at, id LIMIT %s",
        (partner_id, conversation_id, limit),
    )
    return [_clean_row(r) for r in rows]


def get_conversation_turns(partner_id: str, conversation_id: str, limit: int = 6) -> list[dict]:
    """The most recent SUCCESSFUL turns of a conversation, oldest first (for follow-ups)."""
    if _backend is None or not conversation_id:
        return []
    limit = max(1, min(limit, 20))
    rows = _fetch(
        "SELECT question, resolved_question, answer FROM chat_history "
        "WHERE partner_id = %s AND conversation_id = %s AND success = %s AND answer IS NOT NULL "
        "ORDER BY created_at DESC, id DESC LIMIT %s",
        (partner_id, conversation_id, True if _backend == "postgres" else 1, limit),
    )
    return list(reversed(rows))


def list_conversations(partner_id: str, limit: int = 50) -> list[dict]:
    """One row per conversation, newest first: id, title (first question), turns, times."""
    if _backend is None:
        return []
    limit = max(1, min(limit, 100))
    rows = _fetch(
        "SELECT h.conversation_id AS conversation_id, COUNT(*) AS turns, "
        "MIN(h.created_at) AS started_at, MAX(h.created_at) AS updated_at, "
        "(SELECT h2.question FROM chat_history h2 "
        "  WHERE h2.partner_id = h.partner_id AND h2.conversation_id = h.conversation_id "
        "  ORDER BY h2.created_at, h2.id LIMIT 1) AS title "
        "FROM chat_history h WHERE h.partner_id = %s AND h.conversation_id IS NOT NULL "
        "GROUP BY h.partner_id, h.conversation_id ORDER BY MAX(h.created_at) DESC LIMIT %s",
        (partner_id, limit),
    )
    return rows
=======
    return result
>>>>>>> origin/main

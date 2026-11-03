import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from brieflet.config import DB_PATH

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def utc_now_text():
    return datetime.now(UTC).strftime(TIMESTAMP_FORMAT)


def check_db(db_name=DB_PATH):
    """
    Check if the database and tables exist, and create them if they don't.
    """
    Path(db_name).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            description TEXT,
            date TEXT,
            source TEXT NOT NULL,
            first_seen_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL,
            items_fetched INTEGER,
            items_new INTEGER,
            items_deleted INTEGER,
            error TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_to_db(entries, db_name=DB_PATH):
    """
    Save a list of entries to the database.

    Args:
        entries: List of normalized entries to save.
        db_name: Name of the SQLite database file.

    Returns:
        Number of entries that were new (duplicates by link are skipped).
    """
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    inserted = 0
    for entry in entries:
        cur.execute(
            """
            INSERT INTO entries (title, link, description, date, source, first_seen_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (link) DO NOTHING
            """,
            (
                entry["title"],
                entry["link"],
                entry["description"],
                entry["date"],
                entry["source"],
                entry["first_seen_at"],
            ),
        )
        inserted += cur.rowcount
    conn.commit()
    conn.close()
    return inserted


def read_from_db(db_name=DB_PATH):
    """
    Read all entries from the database.

    Args:
        db_name: Name of the SQLite database file.
    Returns:
        List of entries from the database.
    """
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT title, link, description, date, source, first_seen_at FROM entries"
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_old_entries(db_name=DB_PATH):
    cutoff = datetime.now(UTC).replace(microsecond=0) - timedelta(days=7)
    cutoff_text = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = sqlite3.connect(db_name)

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM entries WHERE first_seen_at < ?", (cutoff_text,))
        deleted = cur.rowcount
        conn.commit()
        return deleted
    finally:
        conn.close()


def start_run(db_name=DB_PATH):
    """
    Record the start of a collection run.

    Returns:
        The new run's id, to pass to finish_run.
    """
    conn = sqlite3.connect(db_name)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'running')",
            (utc_now_text(),),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def finish_run(
    run_id,
    status,
    items_fetched=None,
    items_new=None,
    items_deleted=None,
    error=None,
    db_name=DB_PATH,
):
    """
    Record how a collection run ended ('success' or 'failed').
    """
    conn = sqlite3.connect(db_name)
    try:
        conn.execute(
            """
            UPDATE runs
            SET finished_at = ?, status = ?, items_fetched = ?, items_new = ?,
                items_deleted = ?, error = ?
            WHERE id = ?
            """,
            (
                utc_now_text(),
                status,
                items_fetched,
                items_new,
                items_deleted,
                error,
                run_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def read_recent_runs(limit=10, db_name=DB_PATH):
    """
    Read the most recent collection runs, newest first.
    """
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

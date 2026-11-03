import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from brieflet.config import DB_PATH


def check_db(db_name=DB_PATH):
    """
    Check if the database and table exist, and create them if they don't.
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
    conn.commit()
    conn.close()


def save_to_db(entries, db_name=DB_PATH):
    """
    Save a list of entries to the database.

    Args:
        entries: List of normalized entries to save.
        db_name: Name of the SQLite database file.
    """
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
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
    conn.commit()
    conn.close()


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

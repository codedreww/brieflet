import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from brieflet.config import DB_PATH

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def utc_now_text():
    return datetime.now(UTC).strftime(TIMESTAMP_FORMAT)


def connect(db_name):
    conn = sqlite3.connect(db_name)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def check_db(db_name=DB_PATH):
    """
    Check if the database and tables exist, and create them if they don't.
    """
    Path(db_name).parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_name)
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS digests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            digest_date TEXT NOT NULL UNIQUE,
            keywords TEXT NOT NULL,
            created_at TEXT NOT NULL,
            delivered_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS digest_items(
            digest_id INTEGER NOT NULL REFERENCES digests(id),
            rank INTEGER NOT NULL,
            score INTEGER NOT NULL,
            reasons TEXT NOT NULL,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            source TEXT NOT NULL,
            date TEXT,
            description TEXT,
            PRIMARY KEY (digest_id, rank)
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
    conn = connect(db_name)
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
    conn = connect(db_name)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT title, link, description, date, source, first_seen_at FROM entries"
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_setting(key, default=None, db_name=DB_PATH):
    conn = connect(db_name)
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        value = cur.fetchone()
        if value is None:
            return default
        return value[0]
    finally:
        conn.close()


def set_setting(key, value, db_name=DB_PATH):
    conn = connect(db_name)
    updated_at = utc_now_text()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (key, value, updated_at),
        )
        conn.commit()
    finally:
        conn.close()


def delete_old_entries(db_name=DB_PATH):
    cutoff = datetime.now(UTC).replace(microsecond=0) - timedelta(days=7)
    cutoff_text = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = connect(db_name)

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
    conn = connect(db_name)
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
    conn = connect(db_name)
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
    conn = connect(db_name)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def read_unsent_entries(db_name=DB_PATH):
    """
    Read entries that haven't appeared in any digest yet.
    """
    conn = connect(db_name)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT title, link, description, date, source, first_seen_at FROM entries WHERE link NOT IN (SELECT link FROM digest_items)"
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def create_digest(digest_date, keywords, matches, db_name=DB_PATH):
    """
    Store a digest and a snapshot of its items, all-or-nothing.

    Args:
        digest_date: Local date of the digest, 'YYYY-MM-DD'. One digest per date.
        keywords: The keywords the digest was scored with.
        matches: Output of scoring(): a list of [article, score, reasons].

    Returns:
        The new digest's id.

    Raises:
        sqlite3.IntegrityError: If a digest for digest_date already exists.
    """
    conn = connect(db_name)
    try:
        # `with conn` is one transaction: it commits if the block finishes and
        # rolls back every insert if any of them fails, so no half-built digests.
        with conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO digests (digest_date, keywords, created_at) VALUES (?, ?, ?)",
                (digest_date, keywords, utc_now_text()),
            )
            digest_id = cur.lastrowid
            for rank, (article, score, reasons) in enumerate(matches, start=1):
                cur.execute(
                    """
                    INSERT INTO digest_items
                        (digest_id, rank, score, reasons,
                         title, link, source, date, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        digest_id,
                        rank,
                        score,
                        reasons,
                        article["title"],
                        article["link"],
                        article["source"],
                        article.get("date"),
                        article.get("description"),
                    ),
                )
        return digest_id
    finally:
        conn.close()


def get_digest(digest_date, db_name=DB_PATH):
    """
    Read the digest for a date, with its items in rank order.

    Returns:
        A dict of the digest's columns plus "items" (a list of item dicts),
        or None if there's no digest for that date.
    """
    conn = connect(db_name)
    conn.row_factory = sqlite3.Row
    try:
        digest = conn.execute(
            "SELECT * FROM digests WHERE digest_date = ?", (digest_date,)
        ).fetchone()
        if digest is None:
            return None
        items = conn.execute(
            "SELECT * FROM digest_items WHERE digest_id = ? ORDER BY rank",
            (digest["id"],),
        ).fetchall()
        return {**dict(digest), "items": [dict(item) for item in items]}
    finally:
        conn.close()

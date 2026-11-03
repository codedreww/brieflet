import sqlite3
import time
from datetime import UTC, datetime, timedelta

from brieflet.core.db import (
    check_db,
    delete_old_entries,
    read_from_db,
    save_to_db,
)
from brieflet.core.sources.arxiv import normalize_output


def test_normalize_missing_title():
    entry = {
        "link": "https://example.com/article",
        "description": "A sample article.",
    }

    result = normalize_output(entry, source="arxiv")

    assert result is None


def test_normalize_missing_link():
    entry = {
        "title": "Sample Article",
        "description": "A sample article.",
    }

    result = normalize_output(entry, source="arxiv")

    assert result is None


def test_normalize_valid_entry():
    expected_date = "2024-06-01T12:00:00Z"
    entry = {
        "title": "Sample Article",
        "link": "https://example.com/article",
        "description": "A sample article.",
        "published_parsed": time.strptime(expected_date, "%Y-%m-%dT%H:%M:%SZ"),
    }

    result = normalize_output(entry, source="arxiv")

    assert result is not None
    assert result["title"] == entry["title"]
    assert result["link"] == entry["link"]
    assert result["description"] == entry["description"]
    assert result["date"] == expected_date
    assert result["source"] == "arxiv"
    assert result["first_seen_at"]


def test_check_db_creates_table(db_path):
    check_db(db_name=db_path)

    assert db_path.is_file()

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'entries'"
        ).fetchone()
    finally:
        conn.close()

    assert row == ("entries",)


def test_save_to_db_inserts_entries(db_path, saved_entry):
    check_db(db_name=db_path)
    second_entry = {
        **saved_entry,
        "title": "Second Article",
        "link": "https://example.com/article2",
    }
    entries = [saved_entry, second_entry]

    save_to_db(entries, db_name=db_path)

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT title, link, description, date, source, first_seen_at "
            "FROM entries ORDER BY link"
        ).fetchall()
    finally:
        conn.close()

    expected = [
        (
            entry["title"],
            entry["link"],
            entry["description"],
            entry["date"],
            entry["source"],
            entry["first_seen_at"],
        )
        for entry in sorted(entries, key=lambda item: item["link"])
    ]
    assert rows == expected


def test_save_to_db_handles_duplicates(db_path, saved_entry):
    check_db(db_name=db_path)
    save_to_db([saved_entry], db_name=db_path)

    repeated_entry = {
        **saved_entry,
        "first_seen_at": "2024-06-03T09:00:00Z",
    }
    save_to_db([repeated_entry], db_name=db_path)

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT link, first_seen_at FROM entries").fetchall()
    finally:
        conn.close()

    assert rows == [(saved_entry["link"], saved_entry["first_seen_at"])]


def test_read_from_db_returns_saved_entries(db_path, saved_entry):
    check_db(db_name=db_path)
    second_entry = {
        **saved_entry,
        "title": "Second Article",
        "link": "https://example.com/article2",
        "date": None,
    }
    entries = [saved_entry, second_entry]
    save_to_db(entries, db_name=db_path)

    result = read_from_db(db_name=db_path)

    assert sorted(result, key=lambda entry: entry["link"]) == sorted(
        entries, key=lambda entry: entry["link"]
    )


def test_delete_old_entries_removes_only_entries_older_than_seven_days(
    db_path, saved_entry
):
    check_db(db_name=db_path)
    now = datetime.now(UTC).replace(microsecond=0)
    older_entry = {
        **saved_entry,
        "first_seen_at": (now - timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    newer_entry = {
        **saved_entry,
        "title": "Newer Article",
        "link": "https://example.com/newer",
        "first_seen_at": (now - timedelta(days=6)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    save_to_db([older_entry, newer_entry], db_name=db_path)

    deleted = delete_old_entries(db_name=db_path)

    assert deleted == 1
    assert read_from_db(db_name=db_path) == [newer_entry]

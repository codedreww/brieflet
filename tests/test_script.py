import sqlite3
import time

import pytest

from src.script import check_db, normalize_output, save_to_db


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test_storage.db"


@pytest.fixture
def saved_entry():
    return {
        "title": "Sample Article",
        "link": "https://example.com/article",
        "description": "A sample article.",
        "date": "2024-06-01T12:00:00Z",
        "source": "arxiv",
        "first_seen_at": "2024-06-02T09:00:00Z",
    }


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

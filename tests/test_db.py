import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from brieflet.core import db
from brieflet.core.db import (
    check_db,
    connect,
    create_digest,
    delete_old_entries,
    get_digest,
    get_setting,
    read_from_db,
    read_unsent_entries,
    save_to_db,
    set_setting,
)


def test_check_db_creates_tables(db_path):
    check_db(db_name=db_path)

    assert db_path.is_file()

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name != 'sqlite_sequence'"
        ).fetchall()
    finally:
        conn.close()

    assert {name for (name,) in rows} == {
        "entries",
        "runs",
        "settings",
        "digests",
        "digest_items",
    }


def test_digest_items_require_an_existing_digest(db_path):
    check_db(db_name=db_path)

    conn = connect(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            conn.execute(
                "INSERT INTO digest_items "
                "(digest_id, rank, score, reasons, title, link, source) "
                "VALUES (999, 1, 5, 'ai in title', 'T', 'https://x', 'arxiv')"
            )
    finally:
        conn.close()


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


def test_empty_settings_db(db_path):
    check_db(db_name=db_path)
    res = get_setting("key", db_name=db_path)
    assert res is None


def test_get_setting_returns_given_default_when_missing(db_path):
    check_db(db_name=db_path)

    assert get_setting("keywords", default="AI", db_name=db_path) == "AI"


def test_return_settings_db(db_path):
    check_db(db_name=db_path)
    conn = connect(db_path)
    try:
        conn.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES ('keywords', 'Database, Performance', '2024-06-02T09:00:00Z')"
        )
        conn.commit()
    finally:
        conn.close()

    res = get_setting("keywords", db_name=db_path)
    assert res == "Database, Performance"


def count_settings_rows(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT COUNT(*) FROM settings").fetchone()[0]
    finally:
        conn.close()


def read_updated_at(db_path, key):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            "SELECT updated_at FROM settings WHERE key = ?", (key,)
        ).fetchone()[0]
    finally:
        conn.close()


def test_set_setting_inserts_new_key(db_path):
    check_db(db_name=db_path)

    set_setting("keywords", "LLM, agents", db_name=db_path)

    assert get_setting("keywords", db_name=db_path) == "LLM, agents"
    assert count_settings_rows(db_path) == 1


def test_set_setting_twice_updates_the_same_row(db_path, monkeypatch):
    check_db(db_name=db_path)
    timestamps = iter(["2026-11-01T08:00:00Z", "2026-11-02T08:00:00Z"])
    monkeypatch.setattr(db, "utc_now_text", lambda: next(timestamps))

    set_setting("keywords", "a", db_name=db_path)
    set_setting("keywords", "b", db_name=db_path)

    assert get_setting("keywords", db_name=db_path) == "b"
    assert count_settings_rows(db_path) == 1  # an upsert, not two inserts
    assert read_updated_at(db_path, "keywords") == "2026-11-02T08:00:00Z"


def test_set_setting_keeps_other_keys(db_path):
    check_db(db_name=db_path)

    set_setting("keywords", "a", db_name=db_path)
    set_setting("digest_size", "10", db_name=db_path)
    set_setting("keywords", "b", db_name=db_path)

    assert get_setting("keywords", db_name=db_path) == "b"
    assert get_setting("digest_size", db_name=db_path) == "10"
    assert count_settings_rows(db_path) == 2


# --- Digests -----------------------------------------------------------------


def count_rows(db_path, table):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


@pytest.fixture
def stored_articles(db_path, make_article):
    """Three articles saved in `entries`, returned as scoring() would see them."""
    check_db(db_name=db_path)
    articles = [
        make_article(title="Agents for Security", date="2026-10-08T00:00:00Z"),
        make_article(title="Security benchmarks", description="a benchmark"),
        make_article(title="Robotics today"),
    ]
    save_to_db(articles, db_name=db_path)
    return articles


def test_create_digest_round_trip(db_path, stored_articles):
    first, second, _ = stored_articles
    matches = [[first, 7, "security in title"], [second, 5, "security in title"]]

    digest_id = create_digest("2026-11-03", "security", matches, db_name=db_path)
    digest = get_digest("2026-11-03", db_name=db_path)

    assert digest["id"] == digest_id
    assert digest["digest_date"] == "2026-11-03"
    assert digest["keywords"] == "security"
    assert digest["created_at"]
    assert digest["delivered_at"] is None
    assert [item["rank"] for item in digest["items"]] == [1, 2]
    assert [item["title"] for item in digest["items"]] == [
        "Agents for Security",
        "Security benchmarks",
    ]
    top = digest["items"][0]
    assert top["score"] == 7
    assert top["reasons"] == "security in title"
    assert top["link"] == first["link"]
    assert top["date"] == "2026-10-08T00:00:00Z"


def test_create_digest_with_no_matches_stores_an_empty_digest(db_path):
    check_db(db_name=db_path)

    create_digest("2026-11-03", "nothing matches", [], db_name=db_path)

    digest = get_digest("2026-11-03", db_name=db_path)
    assert digest["keywords"] == "nothing matches"
    assert digest["items"] == []


def test_create_digest_is_all_or_nothing(db_path, stored_articles):
    first, second, _ = stored_articles
    broken = {key: value for key, value in second.items() if key != "title"}
    matches = [[first, 7, "security in title"], [broken, 5, "security in title"]]

    with pytest.raises(KeyError):
        create_digest("2026-11-03", "security", matches, db_name=db_path)

    # The digest row and the first item were inserted before the failure;
    # the transaction must have rolled both back.
    assert count_rows(db_path, "digests") == 0
    assert count_rows(db_path, "digest_items") == 0
    assert get_digest("2026-11-03", db_name=db_path) is None


def test_only_one_digest_per_date(db_path, stored_articles):
    create_digest("2026-11-03", "security", [], db_name=db_path)

    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        create_digest("2026-11-03", "security", [], db_name=db_path)


def test_get_digest_missing_date_returns_none(db_path):
    check_db(db_name=db_path)

    assert get_digest("2020-01-01", db_name=db_path) is None


def test_digest_snapshot_survives_entry_deletion(db_path, stored_articles):
    first = stored_articles[0]
    create_digest("2026-11-03", "security", [[first, 7, "x"]], db_name=db_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM entries")
        conn.commit()
    finally:
        conn.close()

    (item,) = get_digest("2026-11-03", db_name=db_path)["items"]
    assert item["title"] == first["title"]
    assert item["link"] == first["link"]


def test_read_unsent_entries_skips_entries_already_in_a_digest(
    db_path, stored_articles
):
    first, second, third = stored_articles
    assert len(read_unsent_entries(db_name=db_path)) == 3

    create_digest("2026-11-03", "security", [[first, 7, "x"]], db_name=db_path)

    unsent_links = {entry["link"] for entry in read_unsent_entries(db_name=db_path)}
    assert unsent_links == {second["link"], third["link"]}


def test_mark_delivered_sets_delivered_at(db_path, monkeypatch):
    check_db(db_name=db_path)
    digest_id = create_digest("2026-11-03", "security", [], db_name=db_path)
    monkeypatch.setattr(db, "utc_now_text", lambda: "2026-11-03T14:00:05Z")

    db.mark_delivered(digest_id, db_name=db_path)

    assert get_digest("2026-11-03", db_name=db_path)["delivered_at"] == (
        "2026-11-03T14:00:05Z"
    )


def test_list_digests_newest_first_with_item_counts(db_path, stored_articles):
    first, second, _ = stored_articles
    create_digest("2026-11-02", "security", [[first, 7, "x"]], db_name=db_path)
    create_digest("2026-11-03", "security", [[second, 5, "y"]], db_name=db_path)
    create_digest("2026-11-01", "nothing", [], db_name=db_path)

    digests = db.list_digests(db_name=db_path)

    assert [d["digest_date"] for d in digests] == ["2026-11-03", "2026-11-02", "2026-11-01"]
    assert [d["item_count"] for d in digests] == [1, 1, 0]
    assert "items" not in digests[0]


def test_list_digests_respects_limit(db_path):
    check_db(db_name=db_path)
    for day in range(1, 6):
        create_digest(f"2026-11-0{day}", "x", [], db_name=db_path)

    assert len(db.list_digests(limit=2, db_name=db_path)) == 2

import sqlite3
from datetime import date
from pathlib import Path

import pytest

from brieflet.core import pipeline
from brieflet.core.db import (
    check_db,
    get_digest,
    read_recent_runs,
    save_to_db,
    set_setting,
)
from brieflet.core.sources.arxiv import FetchError

FIXTURE_FEED = Path(__file__).parent / "fixtures" / "arxiv_cs_ai.xml"
DAY_1 = date(2026, 11, 3)
DAY_2 = date(2026, 11, 4)


@pytest.fixture
def feed_from_fixture(monkeypatch):
    monkeypatch.setattr(
        pipeline, "fetch_rss_feed", lambda url: FIXTURE_FEED.read_bytes()
    )


@pytest.fixture
def feed_fails(monkeypatch):
    def failing_fetch(url):
        raise FetchError("Connection reset by peer")

    monkeypatch.setattr(pipeline, "fetch_rss_feed", failing_fetch)


def count_digests(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT COUNT(*) FROM digests").fetchone()[0]
    finally:
        conn.close()


def links(digest):
    return {item["link"] for item in digest["items"]}


def test_run_daily_builds_and_stores_a_digest(db_path, feed_from_fixture):
    digest = pipeline.run_daily(db_name=db_path, today=DAY_1)

    assert digest["digest_date"] == "2026-11-03"
    assert 0 < len(digest["items"]) <= pipeline.DIGEST_SIZE
    assert [item["rank"] for item in digest["items"]] == list(
        range(1, len(digest["items"]) + 1)
    )
    assert get_digest("2026-11-03", db_name=db_path) == digest


def test_run_daily_respects_limit(db_path, feed_from_fixture):
    digest = pipeline.run_daily(db_name=db_path, today=DAY_1, limit=3)

    assert len(digest["items"]) == 3


def test_run_daily_twice_on_the_same_day_builds_one_digest(
    db_path, feed_from_fixture
):
    first = pipeline.run_daily(db_name=db_path, today=DAY_1)
    second = pipeline.run_daily(db_name=db_path, today=DAY_1)

    assert second == first
    assert count_digests(db_path) == 1


def test_next_day_digest_has_no_repeats(db_path, feed_from_fixture):
    day_1 = pipeline.run_daily(db_name=db_path, today=DAY_1)
    day_2 = pipeline.run_daily(db_name=db_path, today=DAY_2)

    assert day_2["items"], "fixture should have enough matches for two digests"
    assert links(day_1).isdisjoint(links(day_2))


def test_run_daily_uses_saved_keywords(db_path, feed_from_fixture):
    check_db(db_name=db_path)
    set_setting("keywords", "LLM, agents", db_name=db_path)

    digest = pipeline.run_daily(db_name=db_path, today=DAY_1)

    assert digest["keywords"] == "LLM, agents"
    for item in digest["items"]:
        assert "llm" in item["reasons"] or "agents" in item["reasons"]


def test_run_daily_falls_back_to_default_keywords(db_path, feed_from_fixture):
    digest = pipeline.run_daily(db_name=db_path, today=DAY_1)

    assert digest["keywords"] == pipeline.DEFAULT_KEYWORDS


def test_run_daily_with_no_matches_stores_an_empty_digest(
    db_path, feed_from_fixture
):
    check_db(db_name=db_path)
    set_setting("keywords", "zzqx-matches-nothing", db_name=db_path)

    digest = pipeline.run_daily(db_name=db_path, today=DAY_1)

    assert digest["items"] == []
    assert count_digests(db_path) == 1


def test_failed_collect_still_builds_digest_from_stored_entries(
    db_path, feed_fails, make_article
):
    check_db(db_name=db_path)
    stored = make_article(title="Security agents from yesterday")
    save_to_db([stored], db_name=db_path)

    digest = pipeline.run_daily(db_name=db_path, today=DAY_1)

    assert links(digest) == {stored["link"]}
    (run,) = read_recent_runs(db_name=db_path)
    assert run["status"] == "failed"

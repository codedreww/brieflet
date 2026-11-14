from pathlib import Path

import pytest

from brieflet import cli
from brieflet.core import pipeline
from brieflet.core.db import read_from_db, read_recent_runs
from brieflet.core.sources.arxiv import FetchError

FIXTURE_FEED = Path(__file__).parent / "fixtures" / "arxiv_cs_ai.xml"


@pytest.fixture
def feed_from_fixture(monkeypatch):
    # Patch where the name is *used*: collect() looks up fetch_rss_feed in pipeline.
    monkeypatch.setattr(
        pipeline, "fetch_rss_feed", lambda url: FIXTURE_FEED.read_bytes()
    )


def test_collect_records_successful_run(db_path, feed_from_fixture):
    pipeline.collect(db_name=db_path)

    runs = read_recent_runs(db_name=db_path)
    assert len(runs) == 1
    run = runs[0]
    assert run["status"] == "success"
    assert run["items_fetched"] > 0
    assert run["items_new"] == run["items_fetched"]
    assert run["finished_at"] is not None
    assert run["error"] is None
    assert len(read_from_db(db_name=db_path)) == run["items_new"]


def test_second_collect_counts_no_new_items(db_path, feed_from_fixture):
    pipeline.collect(db_name=db_path)
    pipeline.collect(db_name=db_path)

    latest, first = read_recent_runs(db_name=db_path)
    assert latest["items_fetched"] == first["items_fetched"]
    assert latest["items_new"] == 0


def test_collect_records_failed_run_and_reraises(db_path, monkeypatch):
    def failing_fetch(url):
        raise FetchError("Connection reset by peer")

    monkeypatch.setattr(pipeline, "fetch_rss_feed", failing_fetch)

    with pytest.raises(FetchError):
        pipeline.collect(db_name=db_path)

    (run,) = read_recent_runs(db_name=db_path)
    assert run["status"] == "failed"
    assert run["error"] == "Connection reset by peer"
    assert run["finished_at"] is not None


def test_cli_uses_the_pipeline_collect():
    # cli.py should re-use core's collect, not keep its own copy.
    assert cli.collect is pipeline.collect


def test_status_prints_recent_runs(db_path, feed_from_fixture, capsys):
    pipeline.collect(db_name=db_path)

    cli.status(db_name=db_path)

    output = capsys.readouterr().out
    assert "#1" in output
    assert "success" in output
    assert "new=" in output


def test_status_with_no_runs(db_path, capsys):
    cli.status(db_name=db_path)

    assert capsys.readouterr().out == "No runs recorded yet.\n"

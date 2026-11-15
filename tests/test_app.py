"""
Streamlit pages, run for real with AppTest.

conftest's isolated_db fixture points get_db_path() at a temporary database,
and block_network / no_real_webhook keep the pages off arXiv and Discord.
"""

from datetime import date, timedelta
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from brieflet.core import pipeline
from brieflet.core.db import (
    check_db,
    create_digest,
    get_digest,
    get_setting,
    save_to_db,
)
from brieflet.core.delivery.discord import DeliveryError

APP_DIR = Path(__file__).parent.parent / "src" / "brieflet"
FIXTURE_FEED = Path(__file__).parent / "fixtures" / "arxiv_cs_ai.xml"
FAKE_URL = "https://discord.com/api/webhooks/123/fake-token"
TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()


def run_page(name):
    at = AppTest.from_file(str(APP_DIR / name), default_timeout=15)
    return at.run()


def texts(elements):
    return [element.value for element in elements]


def page_text(at):
    """Everything markdown-like on the page, for 'is this shown?' checks."""
    return "\n".join(
        texts(at.markdown) + texts(at.caption) + texts(at.info) + texts(at.subheader)
    )


@pytest.fixture(autouse=True)
def fresh_streamlit_cache():
    st.cache_data.clear()


@pytest.fixture
def store_digest(db_path, make_article):
    check_db(db_name=db_path)

    def store(digest_date, titles, keywords="security"):
        matches = [
            [make_article(title=title, description="about security"), 7, "security in title"]
            for title in titles
        ]
        create_digest(digest_date, keywords, matches, db_name=db_path)

    return store


@pytest.fixture
def webhook_configured(monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", FAKE_URL)


@pytest.fixture
def sent(monkeypatch):
    payloads = []
    monkeypatch.setattr(
        pipeline, "send_discord_webhook", lambda url, payload: payloads.append(payload)
    )
    return payloads


# --- Entry point -------------------------------------------------------------------------


def test_app_opens_on_the_today_page():
    at = run_page("app.py")

    assert not at.exception
    assert texts(at.title) == ["Today's digest"]


# --- Today ---------------------------------------------------------------------------------


def test_today_without_digest_offers_to_build_it():
    at = run_page("app_pages/today.py")

    assert not at.exception
    assert "hasn't been built yet" in at.info[0].value
    assert at.button[0].label == "Build today's digest"


def test_today_build_button_builds_the_digest(db_path, monkeypatch):
    monkeypatch.setattr(
        pipeline, "fetch_rss_feed", lambda url: FIXTURE_FEED.read_bytes()
    )
    at = run_page("app_pages/today.py")

    at.button[0].click().run()

    assert not at.exception
    digest = get_digest(TODAY, db_name=db_path)
    assert digest is not None
    assert texts(at.subheader)[0].startswith("1. ")
    assert len(at.subheader) == len(digest["items"])


def test_today_shows_the_stored_digest(store_digest):
    store_digest(TODAY, ["Agents for Security", "Security benchmarks"])

    at = run_page("app_pages/today.py")

    assert not at.exception
    assert texts(at.subheader) == ["1. Agents for Security", "2. Security benchmarks"]
    assert "Keywords: security" in page_text(at)
    assert "Not sent to Discord" in page_text(at)


def test_today_empty_digest_says_nothing_matched(store_digest):
    store_digest(TODAY, [])

    at = run_page("app_pages/today.py")

    assert "No papers matched" in at.info[0].value


def test_today_hides_send_button_without_webhook(store_digest):
    store_digest(TODAY, ["Agents for Security"])

    at = run_page("app_pages/today.py")

    assert "Send to Discord" not in [button.label for button in at.button]


def test_today_send_button_delivers_once(db_path, store_digest, webhook_configured, sent):
    store_digest(TODAY, ["Agents for Security"])
    at = run_page("app_pages/today.py")

    send = next(button for button in at.button if button.label == "Send to Discord")
    send.click().run()

    assert not at.exception
    assert len(sent) == 1
    assert get_digest(TODAY, db_name=db_path)["delivered_at"] is not None
    assert "Sent to Discord" in page_text(at)
    assert "Send to Discord" not in [button.label for button in at.button]


def test_today_send_failure_shows_an_error(
    db_path, store_digest, webhook_configured, monkeypatch
):
    store_digest(TODAY, ["Agents for Security"])

    def discord_down(url, payload):
        raise DeliveryError("Discord returned HTTP 503")

    monkeypatch.setattr(pipeline, "send_discord_webhook", discord_down)
    at = run_page("app_pages/today.py")

    next(b for b in at.button if b.label == "Send to Discord").click().run()

    assert "Discord returned HTTP 503" in at.error[0].value
    assert get_digest(TODAY, db_name=db_path)["delivered_at"] is None


# --- History -------------------------------------------------------------------------------


def test_history_without_digests():
    at = run_page("app_pages/history.py")

    assert not at.exception
    assert "No digests yet" in at.info[0].value


def test_history_lists_newest_first_and_shows_the_selected_digest(store_digest):
    store_digest(YESTERDAY, ["Yesterday's paper"])
    store_digest(TODAY, ["Today's first", "Today's second"])

    at = run_page("app_pages/history.py")

    assert not at.exception
    assert at.selectbox[0].options[0].endswith("2 papers · not sent")
    assert texts(at.subheader) == ["1. Today's first", "2. Today's second"]

    at.selectbox[0].select(YESTERDAY).run()

    assert texts(at.subheader) == ["1. Yesterday's paper"]


# --- Preferences ---------------------------------------------------------------------------


def test_preferences_start_from_the_defaults():
    at = run_page("app_pages/preferences.py")

    assert not at.exception
    assert at.multiselect[0].value == ["AI", "Security"]
    assert "using the default keywords" in page_text(at)


def test_preferences_save_keywords(db_path):
    at = run_page("app_pages/preferences.py")

    at.multiselect[0].set_value(["LLM", "Agents"])
    at.button[0].click().run()

    assert not at.exception
    assert get_setting("keywords", db_name=db_path) == "LLM, Agents"
    assert "Saved" in at.success[0].value


def test_preferences_refuse_an_empty_list(db_path):
    at = run_page("app_pages/preferences.py")

    at.multiselect[0].set_value([])
    at.button[0].click().run()

    assert "at least one keyword" in at.error[0].value
    check_db(db_name=db_path)
    assert get_setting("keywords", db_name=db_path) is None


# --- Explore -------------------------------------------------------------------------------


def test_explore_scores_stored_papers(db_path, make_article):
    check_db(db_name=db_path)
    save_to_db(
        [
            make_article(title="Security of agents"),
            make_article(title="Robotics today"),
        ],
        db_name=db_path,
    )

    at = run_page("app_pages/explore.py")

    assert not at.exception
    assert texts(at.subheader) == ["1. Security of agents"]
    assert "1 of 2 stored papers shown." in page_text(at)

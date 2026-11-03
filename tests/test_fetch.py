import httpx
import pytest

from brieflet.core.sources import arxiv
from brieflet.core.sources.arxiv import FetchError, fetch_rss_feed

FEED_URL = "https://example.com/feed"


@pytest.fixture
def fake_get(monkeypatch):
    """
    Replace httpx.get with a fake that plays back `outcomes` in order.

    Each outcome is either an exception to raise or a status code to respond with.
    Returns the list of URLs requested, so tests can count attempts.
    """
    calls = []

    def install(*outcomes):
        remaining = list(outcomes)

        def get(url, timeout):
            calls.append(url)
            outcome = remaining.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return httpx.Response(outcome, content=b"<rss/>")

        monkeypatch.setattr(arxiv.httpx, "get", get)
        return calls

    return install


@pytest.fixture
def sleeps():
    """A fake sleep that records the delays instead of waiting."""
    delays = []
    return delays


def test_success_on_first_try_does_not_sleep(fake_get, sleeps):
    calls = fake_get(200)

    content = fetch_rss_feed(FEED_URL, sleep=sleeps.append)

    assert content == b"<rss/>"
    assert len(calls) == 1
    assert sleeps == []


def test_retries_transient_errors_then_succeeds(fake_get, sleeps):
    calls = fake_get(
        httpx.ConnectError("Connection reset by peer"),
        httpx.ReadTimeout("timed out"),
        200,
    )

    content = fetch_rss_feed(FEED_URL, sleep=sleeps.append)

    assert content == b"<rss/>"
    assert len(calls) == 3
    assert sleeps == [1.0, 2.0]  # exponential backoff


def test_retries_server_errors(fake_get, sleeps):
    calls = fake_get(503, 200)

    assert fetch_rss_feed(FEED_URL, sleep=sleeps.append) == b"<rss/>"
    assert len(calls) == 2


def test_gives_up_after_all_attempts(fake_get, sleeps):
    calls = fake_get(*[httpx.ConnectError("Connection reset by peer")] * 3)

    with pytest.raises(FetchError, match="Connection reset by peer") as excinfo:
        fetch_rss_feed(FEED_URL, attempts=3, sleep=sleeps.append)

    assert len(calls) == 3
    assert sleeps == [1.0, 2.0]  # no sleep after the final attempt
    assert isinstance(excinfo.value.__cause__, httpx.ConnectError)


def test_does_not_retry_client_errors(fake_get, sleeps):
    calls = fake_get(404)

    with pytest.raises(FetchError, match="Status code: 404"):
        fetch_rss_feed(FEED_URL, sleep=sleeps.append)

    assert len(calls) == 1
    assert sleeps == []

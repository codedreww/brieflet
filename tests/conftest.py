import httpx
import pytest


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """
    Fail any test that reaches the real network.

    Tests must fake fetching (e.g. patch pipeline.fetch_rss_feed). If a patch
    targets the wrong module, this turns a silent real request into a clear error.
    """

    def blocked(*args, **kwargs):
        raise RuntimeError("Network access is disabled in tests; patch the fetch.")

    monkeypatch.setattr(httpx, "get", blocked)
    monkeypatch.setattr(httpx.Client, "send", blocked)


@pytest.fixture(autouse=True)
def no_real_webhook(monkeypatch):
    """
    Hide the real DISCORD_WEBHOOK_URL that config.py loads from .env.

    Tests that need a webhook set a fake one with monkeypatch.setenv.
    """
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test_storage.db"


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, db_path):
    """
    Point get_db_path() (used by cli.main and the Streamlit pages) at this
    test's temporary database, so no test can open data/storage.db.
    """
    monkeypatch.setenv("BRIEFLET_DB_PATH", str(db_path))


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


@pytest.fixture
def make_article():
    def create_article(
        title="", description="", first_seen_at="2026-10-30T12:00:00Z", date=None
    ):
        return {
            "title": title,
            "link": f"https://arxiv.org/abs/{title}",
            "description": description,
            "date": date,
            "source": "arxiv",
            "first_seen_at": first_seen_at,
        }

    return create_article

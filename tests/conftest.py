import pytest


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

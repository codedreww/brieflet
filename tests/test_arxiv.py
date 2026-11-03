from pathlib import Path

import pytest
import time
from brieflet.core.sources.arxiv import normalize_output, parse_rss_feed


def test_parse_rss_feed_normalizes_arxiv_fixture_entries():
    fixture_path = Path(__file__).parent / "fixtures" / "arxiv_cs_ai.xml"
    rss_feed = fixture_path.read_bytes()

    parsed_feed = parse_rss_feed(rss_feed)

    assert parsed_feed.entries
    for entry in parsed_feed.entries:
        normalized_entry = normalize_output(entry, source="arxiv")
        assert isinstance(normalized_entry, dict)
        assert normalized_entry["source"] == "arxiv"


def test_parse_rss_feed_rejects_invalid_content():
    with pytest.raises(ValueError):
        parse_rss_feed(b"not a feed at all")


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

from pathlib import Path

import pytest

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

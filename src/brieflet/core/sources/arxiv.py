import time

import feedparser
import httpx


def fetch_rss_feed(link: str):
    """
    Fetch RSS feed content from the provided link.

    Args:
        link: URL of the RSS feed.

    Returns:
        Raw RSS feed content as bytes.

    Raises:
        Exception: If the request fails or the response is not successful.
    """
    try:
        response = httpx.get(link, timeout=10.0)
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch RSS feed. Status code: {response.status_code}"
            )
        return response.content
    except httpx.TimeoutException as e:
        raise Exception("Request timed out while fetching the RSS feed.") from e
    except httpx.RequestError as e:
        raise Exception(f"An error occurred while fetching the RSS feed: {e}") from e


def parse_rss_feed(rss_feed: bytes):
    """
    Parse RSS or Atom feed content.

    Args:
        rss_feed: Raw RSS/Atom feed content as bytes.

    Returns:
        Parsed feed data.

    Raises:
        ValueError: If the feed cannot be parsed properly.
    """
    parsed_feed = feedparser.parse(rss_feed)
    if parsed_feed.bozo and not parsed_feed.entries:
        raise ValueError("Failed to parse the RSS feed.")
    return parsed_feed


def normalize_output(entry, source):
    """
    Normalize the output of a feed entry.

    Args:
        entry: A single entry from the parsed feed.
        source: The source of the feed (e.g., 'arxiv').

    Returns:
        A dictionary containing normalized data.
    """
    title = entry.get("title")
    link = entry.get("link")

    if not title or not link:
        if not title:
            print(f"Skipping entry, missing title: {title}")
        if not link:
            print(f"Skipping entry, missing link: {link}")
        return None
    normalized_entry = {
        "title": entry.get("title", None),
        "link": entry.get("link", None),
        "description": entry.get("description", "Description is unavailable"),
        "date": (
            time.strftime("%Y-%m-%dT%H:%M:%SZ", entry.get("published_parsed"))
            if entry.get("published_parsed")
            else None
        ),
        "source": source,
        "first_seen_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return normalized_entry


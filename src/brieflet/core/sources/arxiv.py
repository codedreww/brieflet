import logging
import time

import feedparser
import httpx

logger = logging.getLogger(__name__)

# Server-side or rate-limit statuses that may succeed on a later attempt.
# Other non-200 statuses (404, 403, ...) won't fix themselves, so they fail at once.
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class FetchError(Exception):
    """Raised when a feed can't be fetched."""


def fetch_rss_feed(link: str, attempts=3, base_delay=1.0, sleep=time.sleep):
    """
    Fetch RSS feed content from the provided link, retrying transient failures.

    Timeouts, connection errors and retryable status codes are retried with
    exponential backoff: base_delay, then 2 * base_delay, then 4 * base_delay, ...

    Args:
        link: URL of the RSS feed.
        attempts: Total number of tries before giving up.
        base_delay: Seconds to wait before the first retry.
        sleep: Function used to wait; tests pass a fake to avoid real delays.

    Returns:
        Raw RSS feed content as bytes.

    Raises:
        FetchError: If every attempt fails, or the response status isn't retryable.
    """
    for attempt in range(1, attempts + 1):
        try:
            response = httpx.get(link, timeout=10.0)
        except httpx.TimeoutException as e:
            error = FetchError("Request timed out while fetching the RSS feed.")
            error.__cause__ = e
        except httpx.RequestError as e:
            error = FetchError(f"An error occurred while fetching the RSS feed: {e}")
            error.__cause__ = e
        else:
            if response.status_code == 200:
                return response.content
            error = FetchError(
                f"Failed to fetch RSS feed. Status code: {response.status_code}"
            )
            if response.status_code not in RETRYABLE_STATUS_CODES:
                raise error

        if attempt == attempts:
            raise error
        delay = base_delay * 2 ** (attempt - 1)
        logger.warning(
            "Fetch attempt %d/%d failed (%s); retrying in %.0fs",
            attempt,
            attempts,
            error,
            delay,
        )
        sleep(delay)


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
            logger.warning("Skipping entry, missing title: %s", title)
        if not link:
            logger.warning("Skipping entry, missing link: %s", link)
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


import httpx
import feedparser
import time
import sqlite3


# Function to fetch the RSS feed from a given link
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
    except httpx.TimeoutException:
        raise Exception("Request timed out while fetching the RSS feed.")
    except httpx.RequestError as e:
        raise Exception(f"An error occurred while fetching the RSS feed: {e}")


# Function to parse the RSS feed using feedparser
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


def check_db(db_name="data/storage.db"):
    """
    Check if the database and table exist, and create them if they don't.
    """
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            description TEXT,
            date TEXT,
            source TEXT NOT NULL,
            first_seen_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_to_db(entries, db_name="data/storage.db"):
    """
    Save a list of entries to the database.

    Args:
        entries: List of normalized entries to save.
        db_name: Name of the SQLite database file.
    """
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    for entry in entries:
        cur.execute(
            """
            INSERT INTO entries (title, link, description, date, source, first_seen_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (link) DO NOTHING
        """,
            (
                entry["title"],
                entry["link"],
                entry["description"],
                entry["date"],
                entry["source"],
                entry["first_seen_at"],
            ),
        )
    conn.commit()
    conn.close()


def main():
    check_db()
    input_link = "https://rss.arxiv.org/rss/cs.ai"
    fetched_feed = fetch_rss_feed(input_link)
    parsed_feed = parse_rss_feed(fetched_feed)
    entries = []
    for entry in parsed_feed.entries:
        normalized_entry = normalize_output(entry, source="arxiv")
        if normalized_entry is None:
            continue
        entries.append(normalized_entry)
    save_to_db(entries)
    for i in range(min(5, len(entries))):
        print(entries[i])


if __name__ == "__main__":
    main()

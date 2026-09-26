import httpx
import feedparser
import time
import sqlite3
import re
from datetime import datetime


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


def read_from_db(db_name="data/storage.db"):
    """
    Read all entries from the database.

    Args:
        db_name: Name of the SQLite database file.
    Returns:
        List of entries from the database.
    """
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT title, link, description, date, source, first_seen_at FROM entries"
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def sort_score(matches):
    """
    Sorts matches.

    Args:
        matches: list cointaining [articles, score, reasons]

    Returns:
        sorted matches by descending order on the score and then on the "first_seen" field
    """
    return sorted(
        matches,
        key=lambda match: (
            match[1],
            match[0]["first_seen_at"],
        ),
        reverse=True,
    )


def scoring(keywords, data):
    """
    Scores websites based on keywords inputted by the user.

    Args:
        keywords: words inputted by user.
        data: arcticle found from the database

    Returns:
        Five highest scored arcticle.
    """
    temp = set(keywords.split(","))
    words = set()
    for word in temp:
        cleaned = word.strip().lower()
        words.add(cleaned)

    matches = []

    for arcticle in data:
        title = (arcticle.get("title") or "").lower().strip()
        description = (arcticle.get("description") or "").lower().strip()
        score = 0
        reasons = []

        for word in words:
            pattern = r"\b" + re.escape(word) + r"\b"
            if re.search(pattern, title):
                score += 5
                reasons.append(f"'{word}' in title")

            if re.search(pattern, description):
                score += 2
                reasons.append(f"'{word}' in description")
        if score > 0:
            formatted_reasons = "; ".join(reasons)
            matches.append([arcticle, score, formatted_reasons])

    sorted_matches = sort_score(matches)
    return sorted_matches[:5]


def format_output(result):
    res = ""
    if not result:
        return "No matching articles found."
    for number, entry in enumerate(result, start=1):
        arcticle = entry[0]["title"]
        source = entry[0]["source"]
        score = entry[1] or "0"
        reason = entry[2]
        description = entry[0]["description"]
        link = entry[0]["link"]

        stored_date = entry[0].get("date")
        if stored_date:
            parsed_date = datetime.strptime(stored_date, "%Y-%m-%dT%H:%M:%SZ")
            display_date = parsed_date.strftime("%d %b %Y")
        else:
            display_date = "Publication date unavailable"

        line = f"Article: {arcticle}\nScore: {score} | Source: {source}\nPublished: {display_date}\nLink: {link}\n\nDescription: {description}\nReason: {reason}"
        res += f"{number}.\n{line}\n\n"
    return res


def main():
    """
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
    """
    keywords = input()
    data = read_from_db()
    result = scoring(keywords, data)
    print(format_output(result))


if __name__ == "__main__":
    main()

import sys

from brieflet.core.db import check_db, delete_old_entries, read_from_db, save_to_db
from brieflet.core.formatting import (
    create_markdown,
    format_output_md,
    format_output_txt,
)
from brieflet.core.scoring import scoring
from brieflet.core.sources.arxiv import fetch_rss_feed, normalize_output, parse_rss_feed


def collect():
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
    delete_old_entries()
    print("Collect process is successful")


def search():
    print("Please input keywords divided by commas (,)")
    keywords = input()
    data = read_from_db()
    result = scoring(keywords, data)
    md_res = format_output_md(keywords, result)
    saved_path = create_markdown(md_res)
    print(f"Digest saved to: {saved_path}")
    print(format_output_txt(result))


def main():
    if len(sys.argv) < 2:
        print("Error: Please specify a mode. Usage: brieflet [collect|search].")
        sys.exit(1)
    mode = sys.argv[1].lower()

    if mode == "collect":
        collect()
    elif mode == "search":
        search()
    else:
        print(f"Error: Unknown mode {mode}. Choose 'collect' or 'search'")


if __name__ == "__main__":
    main()

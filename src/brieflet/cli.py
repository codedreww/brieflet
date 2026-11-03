import logging
import sys

from brieflet.config import DB_PATH
from brieflet.core.db import (
    check_db,
    delete_old_entries,
    finish_run,
    read_from_db,
    read_recent_runs,
    save_to_db,
    start_run,
)
from brieflet.core.formatting import (
    create_markdown,
    format_output_md,
    format_output_txt,
)
from brieflet.core.scoring import scoring
from brieflet.core.sources.arxiv import fetch_rss_feed, normalize_output, parse_rss_feed

logger = logging.getLogger(__name__)

ARXIV_FEED_URL = "https://rss.arxiv.org/rss/cs.ai"
USAGE = "Usage: brieflet [collect|search|status]"


def configure_logging():
    # Timestamped lines on stdout, so launchd's collect.stdout.log shows when
    # each run happened and what it did.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def collect(db_name=DB_PATH, feed_url=ARXIV_FEED_URL):
    """
    Fetch the feed, store new entries, prune old ones, and record the run.

    Raises whatever stopped the run, after recording it as failed.
    """
    check_db(db_name=db_name)
    run_id = start_run(db_name=db_name)
    try:
        fetched_feed = fetch_rss_feed(feed_url)
        parsed_feed = parse_rss_feed(fetched_feed)
        entries = []
        for entry in parsed_feed.entries:
            normalized_entry = normalize_output(entry, source="arxiv")
            if normalized_entry is None:
                continue
            entries.append(normalized_entry)
        items_new = save_to_db(entries, db_name=db_name)
        items_deleted = delete_old_entries(db_name=db_name)
    except Exception as e:
        finish_run(run_id, "failed", error=str(e), db_name=db_name)
        raise

    finish_run(
        run_id,
        "success",
        items_fetched=len(entries),
        items_new=items_new,
        items_deleted=items_deleted,
        db_name=db_name,
    )
    logger.info(
        "Collect succeeded: %d fetched, %d new, %d deleted",
        len(entries),
        items_new,
        items_deleted,
    )


def search():
    print("Please input keywords divided by commas (,)")
    keywords = input()
    data = read_from_db()
    result = scoring(keywords, data)
    md_res = format_output_md(keywords, result)
    saved_path = create_markdown(md_res)
    print(f"Digest saved to: {saved_path}")
    print(format_output_txt(result))


def status(db_name=DB_PATH, limit=10):
    """
    Print the most recent collection runs, newest first.
    """
    check_db(db_name=db_name)
    runs = read_recent_runs(limit=limit, db_name=db_name)
    if not runs:
        print("No runs recorded yet.")
        return
    for run in runs:
        line = f"#{run['id']}  {run['started_at']}  {run['status']}"
        if run["status"] == "success":
            line += (
                f"  fetched={run['items_fetched']} new={run['items_new']}"
                f" deleted={run['items_deleted']}"
            )
        elif run["error"]:
            line += f"  error={run['error']}"
        print(line)


def main():
    configure_logging()
    if len(sys.argv) < 2:
        print(f"Error: Please specify a mode. {USAGE}.")
        sys.exit(1)
    mode = sys.argv[1].lower()

    if mode == "collect":
        try:
            collect()
        except Exception:
            logger.exception("Collect failed")
            sys.exit(1)
    elif mode == "search":
        search()
    elif mode == "status":
        status()
    else:
        print(f"Error: Unknown mode {mode}. {USAGE}.")
        sys.exit(1)


if __name__ == "__main__":
    main()

import logging

from brieflet.config import DB_PATH
from brieflet.core.db import (
    check_db,
    delete_old_entries,
    finish_run,
    save_to_db,
    start_run,
)
from brieflet.core.sources.arxiv import fetch_rss_feed, normalize_output, parse_rss_feed

logger = logging.getLogger(__name__)

ARXIV_FEED_URL = "https://rss.arxiv.org/rss/cs.ai"


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

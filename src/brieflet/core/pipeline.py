import logging
from datetime import date

from brieflet.config import DB_PATH
from brieflet.core.db import (
    check_db,
    create_digest,
    delete_old_entries,
    finish_run,
    get_digest,
    get_setting,
    mark_delivered,
    read_unsent_entries,
    save_to_db,
    start_run,
)
from brieflet.core.delivery.discord import build_discord_payload, send_discord_webhook
from brieflet.core.scoring import scoring
from brieflet.core.sources.arxiv import fetch_rss_feed, normalize_output, parse_rss_feed

logger = logging.getLogger(__name__)

ARXIV_FEED_URL = "https://rss.arxiv.org/rss/cs.ai"
DEFAULT_KEYWORDS = "AI, Security"
DIGEST_SIZE = 10


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


def run_daily(db_name=DB_PATH, today=None, limit=DIGEST_SIZE):
    """
    Collect, then build and store today's digest. Safe to run more than once a day.

    Args:
        db_name: SQLite database file.
        today: The local date the digest is for; defaults to date.today().
            Tests pass a fixed date so they don't depend on the real clock.
        limit: Maximum number of items in the digest.

    Returns:
        Today's digest, as returned by get_digest().
    """
    digest_date = (today or date.today()).isoformat()

    # A failed collect shouldn't cancel the digest: entries from earlier runs
    # that were never sent are still worth reading. The failure is already
    # recorded in `runs` by collect().
    try:
        collect(db_name=db_name)
    except Exception:
        logger.warning("Collect failed; building the digest from stored entries")

    existing = get_digest(digest_date, db_name=db_name)
    if existing is not None:
        logger.info("Digest for %s already built; nothing to do", digest_date)
        return existing

    keywords = get_setting("keywords", default=DEFAULT_KEYWORDS, db_name=db_name)
    candidates = read_unsent_entries(db_name=db_name)
    matches = scoring(keywords, candidates, limit=limit)
    create_digest(digest_date, keywords, matches, db_name=db_name)
    logger.info(
        "Built digest for %s: %d items from %d unsent entries (keywords: %s)",
        digest_date,
        len(matches),
        len(candidates),
        keywords,
    )
    return get_digest(digest_date, db_name=db_name)


def deliver_digest(digest, webhook_url, db_name=DB_PATH, force=False):
    """
    Post a digest to Discord once, then record that it was delivered.

    Args:
        digest: A stored digest, as returned by get_digest().
        webhook_url: The Discord webhook URL, or None if delivery isn't set up.
        force: Send even if the digest was already delivered.

    Returns:
        True if the digest was sent, False if it was skipped.

    Raises:
        DeliveryError: If Discord couldn't be reached or rejected the message.
            delivered_at stays empty, so the next run tries again.
    """
    if digest["delivered_at"] and not force:
        logger.info(
            "Digest for %s already delivered at %s; not sending again",
            digest["digest_date"],
            digest["delivered_at"],
        )
        return False
    if not webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL is not set; skipping Discord delivery")
        return False

    send_discord_webhook(webhook_url, build_discord_payload(digest))
    # Only after Discord accepted it: a failed send must stay "not delivered".
    mark_delivered(digest["id"], db_name=db_name)
    logger.info(
        "Delivered digest for %s to Discord (%d items)",
        digest["digest_date"],
        len(digest["items"]),
    )
    return True

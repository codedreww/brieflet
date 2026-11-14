import argparse
import logging
import sys
from datetime import date

from brieflet.config import DB_PATH
from brieflet.core.db import (
    check_db,
    get_digest,
    get_setting,
    read_from_db,
    read_recent_runs,
    set_setting,
)
from brieflet.core.formatting import (
    create_markdown,
    format_digest_txt,
    format_output_md,
    format_output_txt,
)
from brieflet.core.pipeline import DEFAULT_KEYWORDS, collect, run_daily
from brieflet.core.scoring import scoring

logger = logging.getLogger(__name__)


def configure_logging():
    # Timestamped lines on stdout, so launchd's collect.stdout.log shows when
    # each run happened and what it did.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
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


def prefs_show(db_name=DB_PATH):
    """
    Print the saved keywords, or the defaults if none are saved.
    """
    check_db(db_name=db_name)
    keywords = get_setting("keywords", db_name=db_name)
    if keywords is None:
        print(f"Keywords: {DEFAULT_KEYWORDS} (default; none saved)")
    else:
        print(f"Keywords: {keywords}")


def prefs_set(keywords, db_name=DB_PATH):
    """
    Save keywords for future digests. Returns False if there were none to save.
    """
    cleaned = ", ".join(word.strip() for word in keywords.split(",") if word.strip())
    if not cleaned:
        print("Error: give at least one keyword, e.g. brieflet prefs set \"AI, agents\"")
        return False
    check_db(db_name=db_name)
    set_setting("keywords", cleaned, db_name=db_name)
    print(f"Saved keywords: {cleaned}")
    return True


def show_digest(digest_date=None, db_name=DB_PATH):
    """
    Print the stored digest for a date (default: today). Returns False if none.
    """
    digest_date = digest_date or date.today().isoformat()
    check_db(db_name=db_name)
    digest = get_digest(digest_date, db_name=db_name)
    if digest is None:
        print(f"No digest for {digest_date}. Build one with: brieflet run-daily")
        return False
    print(format_digest_txt(digest))
    return True


def iso_date(text):
    """argparse type: accept only YYYY-MM-DD dates."""
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"invalid date {text!r}; use YYYY-MM-DD"
        ) from None


def build_parser():
    parser = argparse.ArgumentParser(
        prog="brieflet",
        description="Personal daily briefing of news and papers.",
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="command")

    commands.add_parser("collect", help="fetch the arXiv feed and store new papers")
    commands.add_parser("search", help="score stored papers against typed keywords")
    commands.add_parser("status", help="show recent collection runs")
    commands.add_parser(
        "run-daily", help="collect, then build and store today's digest"
    )

    prefs = commands.add_parser("prefs", help="show or change your keywords")
    prefs_commands = prefs.add_subparsers(
        dest="prefs_command", required=True, metavar="action"
    )
    prefs_commands.add_parser("show", help="print your saved keywords")
    prefs_set_parser = prefs_commands.add_parser("set", help="save new keywords")
    prefs_set_parser.add_argument(
        "keywords", help='comma-separated keywords, e.g. "LLM, agents, security"'
    )

    digest = commands.add_parser("digest", help="print a stored digest")
    digest.add_argument(
        "--date",
        type=iso_date,
        help="which day's digest, as YYYY-MM-DD (default: today)",
    )
    return parser


def main(argv=None):
    configure_logging()
    args = build_parser().parse_args(argv)

    if args.command == "collect":
        try:
            collect()
        except Exception:
            logger.exception("Collect failed")
            sys.exit(1)
    elif args.command == "search":
        search()
    elif args.command == "status":
        status()
    elif args.command == "run-daily":
        try:
            digest = run_daily()
        except Exception:
            logger.exception("Daily run failed")
            sys.exit(1)
        print(format_digest_txt(digest))
    elif args.command == "prefs":
        if args.prefs_command == "show":
            prefs_show()
        elif not prefs_set(args.keywords):
            sys.exit(1)
    elif args.command == "digest" and not show_digest(args.date):
        sys.exit(1)


if __name__ == "__main__":
    main()

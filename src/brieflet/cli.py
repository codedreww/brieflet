import logging
import sys

from brieflet.config import DB_PATH
from brieflet.core.db import (
    check_db,
    read_from_db,
    read_recent_runs,
)
from brieflet.core.formatting import (
    create_markdown,
    format_output_md,
    format_output_txt,
)
from brieflet.core.pipeline import collect
from brieflet.core.scoring import scoring

logger = logging.getLogger(__name__)
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

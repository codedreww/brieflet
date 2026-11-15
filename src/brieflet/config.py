import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "storage.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
load_dotenv(PROJECT_ROOT / ".env")


def get_db_path():
    """
    The database file to use: BRIEFLET_DB_PATH if set, else data/storage.db.

    Read at call time, so tests can point the CLI and the Streamlit pages at a
    temporary database instead of the real one.
    """
    override = os.environ.get("BRIEFLET_DB_PATH")
    return Path(override) if override else DB_PATH


def get_discord_webhook_url():
    return os.environ.get("DISCORD_WEBHOOK_URL") or None

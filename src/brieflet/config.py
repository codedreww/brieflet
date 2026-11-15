import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "storage.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
load_dotenv(PROJECT_ROOT / ".env")


def get_discord_webhook_url():
    return os.environ.get("DISCORD_WEBHOOK_URL") or None

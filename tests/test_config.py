import importlib
import logging
import os

import dotenv

from brieflet import cli, config

FAKE_URL = "https://discord.com/api/webhooks/123/fake-token"


def test_webhook_url_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", FAKE_URL)

    assert config.get_discord_webhook_url() == FAKE_URL


def test_webhook_url_is_none_when_unset():
    # conftest's no_real_webhook fixture has removed the variable.
    assert "DISCORD_WEBHOOK_URL" not in os.environ
    assert config.get_discord_webhook_url() is None


def test_webhook_url_is_read_at_call_time(monkeypatch):
    # A value set after import must be seen; a constant captured at import wouldn't.
    assert config.get_discord_webhook_url() is None

    monkeypatch.setenv("DISCORD_WEBHOOK_URL", FAKE_URL)

    assert config.get_discord_webhook_url() == FAKE_URL


def test_dotenv_is_loaded_from_the_project_root(monkeypatch):
    # launchd's working directory isn't the repo, so .env must be found by
    # absolute path, not relative to wherever the command was started.
    loaded = []
    monkeypatch.setattr(dotenv, "load_dotenv", lambda path: loaded.append(path))

    importlib.reload(config)

    assert loaded == [config.PROJECT_ROOT / ".env"]
    assert loaded[0].is_absolute()


def test_logging_hides_httpx_request_urls():
    # httpx logs every request URL at INFO; a webhook URL contains its token.
    cli.configure_logging()

    assert logging.getLogger("httpx").getEffectiveLevel() == logging.WARNING
    assert not logging.getLogger("httpx").isEnabledFor(logging.INFO)

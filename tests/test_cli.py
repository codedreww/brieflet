from datetime import date

import pytest

from brieflet import cli
from brieflet.core import pipeline
from brieflet.core.db import check_db, create_digest, get_setting
from brieflet.core.formatting import format_digest_txt

# --- prefs ---------------------------------------------------------------------


def test_prefs_show_reports_defaults_when_nothing_saved(db_path, capsys):
    cli.prefs_show(db_name=db_path)

    assert capsys.readouterr().out == (
        f"Keywords: {pipeline.DEFAULT_KEYWORDS} (default; none saved)\n"
    )


def test_prefs_set_then_show(db_path, capsys):
    assert cli.prefs_set("LLM, agents, security", db_name=db_path) is True
    cli.prefs_show(db_name=db_path)

    output = capsys.readouterr().out
    assert "Saved keywords: LLM, agents, security" in output
    assert output.endswith("Keywords: LLM, agents, security\n")


def test_prefs_set_tidies_spacing_and_empty_pieces(db_path):
    cli.prefs_set("  LLM ,, agents ,  ", db_name=db_path)

    assert get_setting("keywords", db_name=db_path) == "LLM, agents"


def test_prefs_set_rejects_empty_keywords(db_path, capsys):
    assert cli.prefs_set(" , ,", db_name=db_path) is False

    assert "Error" in capsys.readouterr().out
    check_db(db_name=db_path)
    assert get_setting("keywords", db_name=db_path) is None


# --- digest ----------------------------------------------------------------------


@pytest.fixture
def stored_digest(db_path, make_article):
    check_db(db_name=db_path)
    article = make_article(title="Agents for Security", date="2026-10-08T00:00:00Z")
    create_digest(
        "2026-11-03", "security", [[article, 7, "security in title"]], db_name=db_path
    )
    return article


def test_show_digest_prints_stored_digest(db_path, stored_digest, capsys):
    assert cli.show_digest("2026-11-03", db_name=db_path) is True

    output = capsys.readouterr().out
    assert "Digest for 2026-11-03" in output
    assert "1. Agents for Security" in output
    assert "Score: 7" in output
    assert "Published: 08 Oct 2026" in output
    assert "Why: security in title" in output
    assert stored_digest["link"] in output


def test_show_digest_missing_date(db_path, capsys):
    assert cli.show_digest("2020-01-01", db_name=db_path) is False

    assert "No digest for 2020-01-01" in capsys.readouterr().out


def test_format_digest_txt_empty_digest():
    digest = {
        "digest_date": "2026-11-03",
        "keywords": "zzqx",
        "delivered_at": None,
        "items": [],
    }

    text = format_digest_txt(digest)

    assert "Delivered: not yet" in text
    assert text.endswith("No matching articles found.")


# --- argument parsing --------------------------------------------------------------


def test_parser_reads_prefs_set():
    args = cli.build_parser().parse_args(["prefs", "set", "LLM, agents"])

    assert args.command == "prefs"
    assert args.prefs_command == "set"
    assert args.keywords == "LLM, agents"


def test_parser_reads_digest_date():
    args = cli.build_parser().parse_args(["digest", "--date", "2026-11-03"])

    assert args.date == "2026-11-03"


def test_parser_digest_date_defaults_to_none():
    assert cli.build_parser().parse_args(["digest"]).date is None


@pytest.mark.parametrize(
    "argv",
    [
        [],  # no command
        ["bogus"],  # unknown command
        ["prefs"],  # prefs without show/set
        ["prefs", "set"],  # set without keywords
        ["digest", "--date", "2026-13-01"],  # impossible date
        ["digest", "--date", "yesterday"],  # not YYYY-MM-DD
    ],
)
def test_parser_rejects_bad_input(argv, capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.build_parser().parse_args(argv)

    assert excinfo.value.code == 2  # argparse's "usage error" exit code


# --- main() wiring -----------------------------------------------------------------


@pytest.fixture
def fake_run_daily(monkeypatch):
    calls = []

    def run_daily():
        calls.append(True)
        return {
            "digest_date": date.today().isoformat(),
            "keywords": "AI",
            "delivered_at": None,
            "items": [],
        }

    monkeypatch.setattr(cli, "run_daily", run_daily)
    return calls


def test_main_run_daily_prints_the_digest(fake_run_daily, capsys):
    cli.main(["run-daily"])

    assert fake_run_daily == [True]
    assert "No matching articles found." in capsys.readouterr().out


def test_main_run_daily_exits_1_on_failure(monkeypatch):
    def broken():
        raise RuntimeError("disk full")

    monkeypatch.setattr(cli, "run_daily", broken)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["run-daily"])

    assert excinfo.value.code == 1


def test_main_prefs_set_with_only_commas_exits_1(monkeypatch):
    # main() calls handlers without db_name, which would open the real
    # data/storage.db, so main() tests always replace the handler.
    monkeypatch.setattr(cli, "prefs_set", lambda keywords: False)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["prefs", "set", " , "])

    assert excinfo.value.code == 1

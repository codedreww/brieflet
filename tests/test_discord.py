import httpx
import pytest

from brieflet.core.delivery import discord
from brieflet.core.delivery.discord import (
    DESCRIPTION_LIMIT,
    TITLE_LIMIT,
    DeliveryError,
    build_discord_payload,
    send_discord_webhook,
    truncate,
)

FAKE_URL = "https://discord.com/api/webhooks/123/secret-token-abc"


def make_item(rank, title="Agents for Security", **overrides):
    item = {
        "rank": rank,
        "score": 7,
        "reasons": "security in title",
        "title": title,
        "link": f"https://arxiv.org/abs/2611.0000{rank}",
        "source": "arxiv",
        "date": "2026-11-10T00:00:00Z",
        "description": "An abstract.",
    }
    return {**item, **overrides}


def make_digest(items, keywords="LLM, agents, security"):
    return {
        "id": 1,
        "digest_date": "2026-11-15",
        "keywords": keywords,
        "created_at": "2026-11-15T14:00:00Z",
        "delivered_at": None,
        "items": items,
    }


# --- truncate ------------------------------------------------------------------------


def test_truncate_leaves_short_text_alone():
    assert truncate("short", 10) == "short"
    assert truncate("exactly10!", 10) == "exactly10!"


def test_truncate_never_exceeds_the_limit():
    result = truncate("x" * 300, 256)

    assert len(result) == 256
    assert result.endswith("…")


# --- build_discord_payload ---------------------------------------------------------------


def test_payload_has_one_embed_per_item_in_rank_order():
    digest = make_digest([make_item(1, "First paper"), make_item(2, "Second paper")])

    payload = build_discord_payload(digest)

    assert [embed["title"] for embed in payload["embeds"]] == [
        "1. First paper",
        "2. Second paper",
    ]


def test_payload_header_mentions_date_count_and_keywords():
    payload = build_discord_payload(make_digest([make_item(1), make_item(2)]))

    assert "2026-11-15" in payload["content"]
    assert "2 papers" in payload["content"]
    assert "LLM, agents, security" in payload["content"]


def test_payload_header_uses_singular_for_one_paper():
    payload = build_discord_payload(make_digest([make_item(1)]))

    assert "1 paper " in payload["content"]


def test_embed_links_score_reasons_and_footer():
    (embed,) = build_discord_payload(make_digest([make_item(1)]))["embeds"]

    assert embed["url"] == "https://arxiv.org/abs/2611.00001"
    assert embed["description"] == "**Score 7** · security in title"
    assert embed["footer"]["text"] == "arxiv · Published 10 Nov 2026"


def test_embed_footer_handles_missing_publication_date():
    (embed,) = build_discord_payload(make_digest([make_item(1, date=None)]))["embeds"]

    assert embed["footer"]["text"] == "arxiv · Published Publication date unavailable"


def test_long_titles_and_descriptions_fit_discord_limits():
    item = make_item(1, title="T" * 1000, reasons="r" * 10_000)

    (embed,) = build_discord_payload(make_digest([item]))["embeds"]

    assert len(embed["title"]) == TITLE_LIMIT
    assert len(embed["description"]) == DESCRIPTION_LIMIT


def test_payload_never_has_more_than_ten_embeds():
    digest = make_digest([make_item(rank) for rank in range(1, 13)])

    assert len(build_discord_payload(digest)["embeds"]) == 10


def test_empty_digest_sends_a_message_without_embeds():
    payload = build_discord_payload(make_digest([]))

    assert "embeds" not in payload
    assert "no papers matched" in payload["content"]
    assert "2026-11-15" in payload["content"]


def test_paper_titles_cannot_ping_everyone():
    item = make_item(1, title="@everyone look at this")

    payload = build_discord_payload(make_digest([item]))

    assert payload["allowed_mentions"] == {"parse": []}


# --- send_discord_webhook -------------------------------------------------------------------


@pytest.fixture
def fake_post(monkeypatch):
    """
    Replace httpx.post with a fake that plays back outcomes in order.

    Each outcome is an exception to raise, a status code, or (status, json_body).
    Returns the list of calls as (url, payload) pairs.
    """
    calls = []

    def install(*outcomes):
        remaining = list(outcomes)

        def post(url, json, timeout):
            calls.append((url, json))
            outcome = remaining.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            if isinstance(outcome, tuple):
                status, body = outcome
                return httpx.Response(status, json=body)
            return httpx.Response(outcome)

        monkeypatch.setattr(discord.httpx, "post", post)
        return calls

    return install


@pytest.fixture
def sleeps():
    return []


PAYLOAD = {"content": "hello"}


def test_204_is_success(fake_post, sleeps):
    calls = fake_post(204)

    send_discord_webhook(FAKE_URL, PAYLOAD, sleep=sleeps.append)

    assert calls == [(FAKE_URL, PAYLOAD)]
    assert sleeps == []


def test_rate_limit_waits_for_retry_after(fake_post, sleeps):
    calls = fake_post((429, {"retry_after": 2.5}), 204)

    send_discord_webhook(FAKE_URL, PAYLOAD, sleep=sleeps.append)

    assert len(calls) == 2
    assert sleeps == [2.5]


def test_server_errors_and_connection_errors_back_off(fake_post, sleeps):
    calls = fake_post(503, httpx.ConnectError("Connection reset by peer"), 204)

    send_discord_webhook(FAKE_URL, PAYLOAD, sleep=sleeps.append)

    assert len(calls) == 3
    assert sleeps == [1.0, 2.0]


def test_client_errors_fail_immediately(fake_post, sleeps):
    calls = fake_post((404, {"message": "Unknown Webhook", "code": 10015}))

    with pytest.raises(DeliveryError, match=r"HTTP 404.*Unknown Webhook"):
        send_discord_webhook(FAKE_URL, PAYLOAD, sleep=sleeps.append)

    assert len(calls) == 1
    assert sleeps == []


def test_gives_up_after_all_attempts(fake_post, sleeps):
    calls = fake_post(502, 502, 502)

    with pytest.raises(DeliveryError, match="HTTP 502"):
        send_discord_webhook(FAKE_URL, PAYLOAD, attempts=3, sleep=sleeps.append)

    assert len(calls) == 3
    assert sleeps == [1.0, 2.0]


@pytest.mark.parametrize(
    "outcome",
    [
        (400, {"message": "Invalid Form Body"}),
        httpx.ConnectError("Connection reset by peer"),
        httpx.ReadTimeout("timed out"),
    ],
    ids=["rejected", "unreachable", "timeout"],
)
def test_errors_never_reveal_the_webhook_token(fake_post, sleeps, outcome):
    fake_post(*[outcome] * 3)

    with pytest.raises(DeliveryError) as excinfo:
        send_discord_webhook(FAKE_URL, PAYLOAD, sleep=sleeps.append)

    assert "secret-token-abc" not in str(excinfo.value)


def test_retry_warnings_never_reveal_the_webhook_token(fake_post, sleeps, caplog):
    fake_post(503, 204)

    send_discord_webhook(FAKE_URL, PAYLOAD, sleep=sleeps.append)

    assert "retrying" in caplog.text
    assert "secret-token-abc" not in caplog.text

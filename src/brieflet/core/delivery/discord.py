import logging
import time

import httpx

from brieflet.core.formatting import convert_date

logger = logging.getLogger(__name__)

# Discord's limits for one webhook message.
CONTENT_LIMIT = 2000
TITLE_LIMIT = 256
DESCRIPTION_LIMIT = 4096
FOOTER_LIMIT = 2048
MAX_EMBEDS = 10

EMBED_COLOR = 0x5865F2
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}


class DeliveryError(Exception):
    """Raised when a digest can't be delivered to Discord."""


def truncate(text, limit):
    """
    Shorten text to at most `limit` characters, marking the cut with "…".
    """
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def build_discord_payload(digest):
    """
    Turn a stored digest (as returned by get_digest) into a webhook message.

    One embed per item, in rank order, within Discord's length limits.
    """
    items = digest["items"][:MAX_EMBEDS]
    date = digest["digest_date"]
    keywords = digest["keywords"]
    # Paper titles are untrusted text: never let them ping @everyone or roles.
    no_pings = {"parse": []}

    if not items:
        content = (
            f"📚 **Brieflet digest for {date}**: no papers matched your keywords "
            f"today (keywords: {keywords})."
        )
        return {"content": truncate(content, CONTENT_LIMIT), "allowed_mentions": no_pings}

    noun = "paper" if len(items) == 1 else "papers"
    content = (
        f"📚 **Brieflet digest for {date}** — {len(items)} {noun} "
        f"(keywords: {keywords})"
    )
    embeds = [
        {
            "title": truncate(f"{item['rank']}. {item['title']}", TITLE_LIMIT),
            "url": item["link"],
            "description": truncate(
                f"**Score {item['score']}** · {item['reasons']}", DESCRIPTION_LIMIT
            ),
            "footer": {
                "text": truncate(
                    f"{item['source']} · Published {convert_date(item['date'])}",
                    FOOTER_LIMIT,
                )
            },
            "color": EMBED_COLOR,
        }
        for item in items
    ]
    return {
        "content": truncate(content, CONTENT_LIMIT),
        "embeds": embeds,
        "allowed_mentions": no_pings,
    }


def retry_after_seconds(response, fallback):
    """
    How long Discord asked us to wait after a 429, in seconds.
    """
    try:
        return float(response.json()["retry_after"])
    except (ValueError, KeyError, TypeError):
        pass
    try:
        return float(response.headers["Retry-After"])
    except (KeyError, ValueError):
        return fallback


def send_discord_webhook(url, payload, attempts=3, base_delay=1.0, sleep=time.sleep):
    """
    Post a message to a Discord webhook, retrying transient failures.

    Rate limits (429) wait for Discord's retry_after; timeouts, connection errors
    and 5xx responses back off exponentially. Other 4xx responses fail at once.
    The webhook URL contains its secret token, so it never appears in errors or logs.

    Raises:
        DeliveryError: If every attempt fails, or Discord rejects the request.
    """
    for attempt in range(1, attempts + 1):
        backoff = base_delay * 2 ** (attempt - 1)
        try:
            response = httpx.post(url, json=payload, timeout=10.0)
        except httpx.TimeoutException as e:
            error = DeliveryError("Timed out posting to the Discord webhook")
            error.__cause__ = e
            delay = backoff
        except httpx.RequestError as e:
            error = DeliveryError(f"Could not reach the Discord webhook: {e}")
            error.__cause__ = e
            delay = backoff
        else:
            status = response.status_code
            if 200 <= status < 300:
                return
            if status == 429:
                error = DeliveryError("Discord rate-limited the webhook (HTTP 429)")
                delay = retry_after_seconds(response, fallback=backoff)
            elif status in RETRYABLE_STATUS_CODES:
                error = DeliveryError(f"Discord returned HTTP {status}")
                delay = backoff
            else:
                raise DeliveryError(
                    f"Discord rejected the webhook request (HTTP {status}): "
                    f"{truncate(response.text, 300)}"
                )

        if attempt == attempts:
            raise error
        logger.warning(
            "Discord delivery attempt %d/%d failed (%s); retrying in %.1fs",
            attempt,
            attempts,
            error,
            delay,
        )
        sleep(delay)

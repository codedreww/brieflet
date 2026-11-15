"""
Streamlit building blocks shared by the pages in app_pages/.

This is an entry-point layer like cli.py: it may import core/, but core/ must
never import it.
"""

from datetime import UTC, datetime

import streamlit as st

from brieflet.core.db import TIMESTAMP_FORMAT
from brieflet.core.formatting import convert_date


def local_time(utc_text):
    """
    Turn a stored UTC timestamp ('2026-11-15T14:00:05Z') into local time text.
    """
    moment = datetime.strptime(utc_text, TIMESTAMP_FORMAT).replace(tzinfo=UTC)
    return moment.astimezone().strftime("%d %b %Y, %H:%M")


def split_keywords(text):
    """
    'LLM, agents ,, security' -> ['LLM', 'agents', 'security']
    """
    return [word.strip() for word in text.split(",") if word.strip()]


def render_item(item, key_prefix):
    """
    One paper as a card: title, score, why it matched, abstract and links.

    `item` needs rank, title, link, source, date, description, score, reasons;
    a digest item from get_digest() has all of them.
    """
    with st.container(border=True):
        st.subheader(f"{item['rank']}. {item['title']}")
        with st.container(horizontal=True, vertical_alignment="center"):
            st.badge(f"Score {item['score']}", icon=":material/star:", color="primary")
            st.caption(f"{item['source']} · Published {convert_date(item['date'])}")
        st.markdown(f"**Why it matched:** {item['reasons']}")

        with st.expander("Read abstract"):
            st.write(item.get("description") or "Abstract unavailable.")

        link = item["link"]
        is_arxiv = "arxiv.org/abs/" in link
        pdf_url = link.replace("/abs/", "/pdf/", 1) if is_arxiv else None
        with st.container(horizontal=True):
            st.link_button("Open article", link, icon=":material/open_in_new:")
            if pdf_url:
                st.link_button("Open PDF", pdf_url, icon=":material/picture_as_pdf:")

        if pdf_url and st.toggle("Preview PDF", key=f"{key_prefix}-preview-{link}"):
            st.pdf(pdf_url, height=650, key=f"{key_prefix}-pdf-{link}")


def render_digest_summary(digest):
    """
    Badges for a digest: its keywords and whether it reached Discord.
    """
    with st.container(horizontal=True):
        st.badge(f"Keywords: {digest['keywords']}", icon=":material/sell:", color="blue")
        if digest["delivered_at"]:
            st.badge(
                f"Sent to Discord {local_time(digest['delivered_at'])}",
                icon=":material/check_circle:",
                color="green",
            )
        else:
            st.badge("Not sent to Discord", icon=":material/schedule_send:", color="gray")


def render_digest_items(digest, key_prefix):
    if not digest["items"]:
        st.info(
            "No papers matched your keywords for this digest.",
            icon=":material/search_off:",
        )
        return
    for item in digest["items"]:
        render_item(item, key_prefix=key_prefix)

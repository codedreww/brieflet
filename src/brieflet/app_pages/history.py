from datetime import date

import streamlit as st

from brieflet.config import get_db_path
from brieflet.core.db import check_db, get_digest, list_digests
from brieflet.ui import render_digest_items, render_digest_summary

db_path = get_db_path()
check_db(db_name=db_path)
digests = list_digests(db_name=db_path)

st.title("History")

if not digests:
    st.info(
        "No digests yet. Your first one appears after the next daily run, or "
        "build it from the Today page.",
        icon=":material/history:",
    )
    st.stop()

by_date = {digest["digest_date"]: digest for digest in digests}


def describe(digest_date):
    digest = by_date[digest_date]
    day = date.fromisoformat(digest_date).strftime("%a %d %b %Y")
    count = digest["item_count"]
    papers = "paper" if count == 1 else "papers"
    sent = "sent" if digest["delivered_at"] else "not sent"
    return f"{day} · {count} {papers} · {sent}"


selected = st.selectbox(
    "Digest",
    options=list(by_date),
    format_func=describe,
    help="Newest first. Each digest keeps the papers and keywords it was built with.",
)

digest = get_digest(selected, db_name=db_path)
render_digest_summary(digest)
render_digest_items(digest, key_prefix=f"history-{selected}")

from datetime import date

import streamlit as st

from brieflet.config import get_db_path, get_discord_webhook_url
from brieflet.core.db import check_db, get_digest
from brieflet.core.delivery.discord import DeliveryError
from brieflet.core.pipeline import deliver_digest, run_daily
from brieflet.ui import render_digest_items, render_digest_summary

db_path = get_db_path()
check_db(db_name=db_path)
today = date.today()
digest = get_digest(today.isoformat(), db_name=db_path)

st.title("Today's digest")
st.caption(today.strftime("%A, %d %B %Y"))

if digest is None:
    st.info(
        "Today's digest hasn't been built yet. It's built automatically at 08:00, "
        "or you can build it now.",
        icon=":material/schedule:",
    )
    if st.button("Build today's digest", icon=":material/auto_awesome:", type="primary"):
        with st.spinner("Collecting papers and building your digest..."):
            run_daily(db_name=db_path, today=today)
        st.rerun()
    st.stop()

render_digest_summary(digest)

webhook_url = get_discord_webhook_url()
if (
    not digest["delivered_at"]
    and webhook_url
    and st.button("Send to Discord", icon=":material/send:")
):
    try:
        deliver_digest(digest, webhook_url, db_name=db_path)
    except DeliveryError as e:
        st.error(f"Discord delivery failed: {e}", icon=":material/error:")
    else:
        st.rerun()

render_digest_items(digest, key_prefix="today")

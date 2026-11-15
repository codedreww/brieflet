import streamlit as st

from brieflet.config import get_db_path
from brieflet.core.db import check_db, get_setting, read_from_db
from brieflet.core.pipeline import DEFAULT_KEYWORDS
from brieflet.core.scoring import scoring
from brieflet.ui import render_item, split_keywords


@st.cache_data(ttl="5m", max_entries=4)
def load_entries(db_path):
    # Every stored paper (about a week's worth); cached so typing keywords
    # doesn't re-read the database on each rerun.
    return read_from_db(db_name=db_path)


db_path = get_db_path()
check_db(db_name=db_path)
saved = split_keywords(get_setting("keywords", db_name=db_path) or DEFAULT_KEYWORDS)

st.title("Explore")
st.write(
    "Try keywords against every paper collected this week. Nothing here changes "
    "your saved preferences or your digests."
)

keywords = st.multiselect(
    "Keywords",
    options=saved,
    default=saved,
    accept_new_options=True,
    placeholder="Pick or type keywords",
)
limit = st.segmented_control("Show", options=[5, 10, 20], default=10, format_func=lambda n: f"Top {n}")

entries = load_entries(db_path)
matches = scoring(", ".join(keywords), entries, limit=limit or 10)
st.caption(f"{len(matches)} of {len(entries)} stored papers shown.")

if not matches:
    st.info("No papers match these keywords.", icon=":material/search_off:")
for rank, (article, score, reasons) in enumerate(matches, start=1):
    render_item(
        {**article, "rank": rank, "score": score, "reasons": reasons},
        key_prefix="explore",
    )

import streamlit as st

from brieflet.config import get_db_path
from brieflet.core.db import check_db, get_setting, set_setting
from brieflet.core.pipeline import DEFAULT_KEYWORDS
from brieflet.ui import split_keywords

SUGGESTIONS = ["AI", "Security", "Robotics", "Machine Learning", "LLM", "Agents", "Benchmark"]

db_path = get_db_path()
check_db(db_name=db_path)
saved = get_setting("keywords", db_name=db_path)
current = split_keywords(saved or DEFAULT_KEYWORDS)

st.title("Preferences")
st.write(
    "Brieflet ranks new papers against these keywords: **5 points** for each "
    "keyword in a paper's title and **2** for each in its abstract."
)
if saved is None:
    st.caption("You're using the default keywords. Save your own below.")

with st.form("keywords_form"):
    chosen = st.multiselect(
        "Keywords",
        options=list(dict.fromkeys(current + SUGGESTIONS)),
        default=current,
        accept_new_options=True,
        placeholder="Pick or type keywords",
        help="Type a new keyword and press Enter to add it.",
    )
    submitted = st.form_submit_button(
        "Save keywords", icon=":material/save:", type="primary"
    )

if submitted:
    if not chosen:
        st.error("Choose at least one keyword.", icon=":material/error:")
    else:
        set_setting("keywords", ", ".join(chosen), db_name=db_path)
        st.success(
            "Saved. The next digest will use these keywords; a digest that's "
            "already built keeps the keywords it was made with.",
            icon=":material/check_circle:",
        )

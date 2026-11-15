# Streamlit entry point: `streamlit run src/brieflet/app.py`.
# This file only sets up navigation; each page lives in app_pages/.

import streamlit as st

st.set_page_config(page_title="Brieflet", page_icon=":material/newspaper:")

page = st.navigation(
    [
        st.Page(
            "app_pages/today.py", title="Today", icon=":material/today:", default=True
        ),
        st.Page("app_pages/history.py", title="History", icon=":material/history:"),
        st.Page(
            "app_pages/preferences.py", title="Preferences", icon=":material/tune:"
        ),
        st.Page("app_pages/explore.py", title="Explore", icon=":material/search:"),
    ],
    position="top",
)
page.run()

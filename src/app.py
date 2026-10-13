import streamlit as st
from script import read_from_db, scoring
from datetime import datetime, timedelta, timezone

st.header("Welcome to Pscript!📚📖")
st.write(
    " Add your keywords below and we'll find the best recent articles from Arxiv for you to read!"
)

with st.container(border=True):
    keywords = st.multiselect(
        "Choose or add your interests",
        options=["AI", "Security", "Robotics", "Machine Learning", "LLM", "Benchmark"],
        default=["AI", "Security"],
        accept_new_options=True,
    )

st.write("Relevant articles based on keywords:")


def get_results(selected_keywords):
    keyword_text = ", ".join(selected_keywords)
    data = read_from_db()
    return scoring(keyword_text, data)


def format_output(results):
    if not results:
        res += "No matching articles found."

    for number, entry in enumerate(results, start=1):
        article = entry[0]["title"]
        source = entry[0]["source"]
        score = entry[1] or "0"
        reason = entry[2]
        description = entry[0].get("description") or "Description unavailable"
        link = entry[0]["link"]

        with st.container(border=True):
            stored_date = entry[0].get("date")
            if stored_date:
                parsed_date = datetime.strptime(stored_date, "%Y-%m-%dT%H:%M:%SZ")
                display_date = parsed_date.strftime("%d %b %Y")
            else:
                display_date = "Publication date unavailable"

            st.subheader(f"{number}) {article}")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"date published: {display_date}")
            with col2:
                st.caption(f"{source} · Match score: {score}")
            st.write(f"**Why it matched:** {reason}")

            with st.expander("Read abstract"):
                st.write(description)

            col3, col4 = st.columns(2)
            with col3:
                st.link_button("Open article", link)

            pdf_url = link.replace("/abs/", "/pdf/", 1)
            with col4:
                st.link_button("Open PDF in browser", pdf_url)

            if st.toggle("Preview PDF", key=f"preview-{link}"):
                st.pdf(pdf_url, height=650, key=f"pdf-{link}")


results = get_results(keywords)
format_output(results)

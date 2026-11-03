from brieflet.core.formatting import format_output_md, format_output_txt
from brieflet.core.scoring import scoring


def test_format_output_txt_returns_no_matching_articles():
    result = ""
    assert format_output_txt(result) == "No matching articles found."


def test_format_output_txt_formats_stored_date(make_article):
    article = make_article(title="Agents for Security", date="2026-10-08T00:00:00Z")
    result = [[article, 5, "agents in title"]]

    output = format_output_txt(result)

    assert "Published: 08 Oct 2026" in output


def test_format_output_txt_handles_missing_date(make_article):
    article = make_article(title="Agents for Security", date=None)
    result = [[article, 5, "agents in title"]]

    output = format_output_txt(result)

    assert "Published: Publication date unavailable" in output


def test_format_output_md_includes_keywords_numbered_heading(make_article):
    keywords = "agents, security"
    data = [
        make_article(
            title="Agents for Security",
            description="agents for security is very important i swear... please trust me!",
            first_seen_at="2026-10-29T12:00:00Z",
        ),
        make_article(title="Security Research", first_seen_at="2026-10-28T12:00:00Z"),
    ]

    result = scoring(keywords, data)
    output = format_output_md(keywords, result)

    assert "Keywords: agents, security\n" in output
    assert "#### 1. Agents for Security\n" in output
    assert "#### 2. Security Research\n" in output
    assert "Generated: " in output

from brieflet.script import scoring


def test_title_match_scores_five(make_article):
    # Arrange: set up the input
    data = [make_article(title="Agents for Security")]

    # Act: call the thing being tested, ONCE
    result = scoring("security", data)

    # Assert: check the output
    assert len(result) == 1
    article, score, reasons = result[0]
    assert score == 5
    assert reasons == "security in title"


def test_description_match_scores_two(make_article):
    # Arrange
    data = [make_article(description="The big bad wolf of wallstreet is AI")]

    # Act
    result = scoring("AI", data)

    # Assert
    assert len(result) == 1
    article, score, reasons = result[0]
    assert score == 2
    assert reasons == "ai in description"


def test_title_and_description_match_scores_seven(make_article):
    data = [
        make_article(
            title="Agents for Security",
            description="agents for security is very important i swear... please trust me!",
        )
    ]
    result = scoring("Agents", data)

    assert len(result) == 1
    article, score, reasons = result[0]
    assert score == 7
    assert reasons == "agents in description; agents in title"


def test_matching_ignore_letter_case(make_article):
    data = [
        make_article(description="AI IS EVIL"),
        make_article(description="ai is good trust me bro"),
    ]

    result = scoring("Ai", data)
    assert len(result) == 2
    article1, score1, reasons1 = result[0]
    article2, score2, reasons2 = result[1]
    assert reasons1 == reasons2


# Note: TODO
def test_words_with_prurals_should_be_detected(make_article):
    data = [make_article(title="LLMs is not it ma g")]

    result = scoring("LLM", data)

    assert len(result) == 1
    article, score, reasons = result[0]
    assert score == 5
    assert reasons == "llm in title"


def test_keywords_are_split_with_commas_and_whitespaces_emptyplaces_ignored(
    make_article,
):
    data = [make_article(description="The big bad wolf of wallstreet is AI")]

    result = scoring(" AI, wallstreet", data)

    assert len(result) == 1
    article, score, reasons = result[0]
    assert score == 4

    assert reasons == "ai, wallstreet in description"


# TODO
def test_special_characters_in_scoring(make_article):
    data = [make_article(title="I do not like C++")]

    result = scoring("C++", data)

    assert len(result) == 1
    article, score, reasons = result[0]
    assert score == 5
    assert reasons == "c++ in title"


def test_no_matches(make_article):
    data = [make_article(title="I do not like C++")]

    result = scoring("AI", data)

    assert len(result) == 0
    assert result == []


def test_only_top_five_articles_are_returned(make_article):
    data = [
        make_article(
            title=f"Security article {number}",
            description="security" if number >= 3 else "",
        )
        for number in range(8)
    ]

    result = scoring("security", data)

    assert len(result) == 5
    assert {article["title"] for article, score, reasons in result} == {
        f"Security article {number}" for number in range(3, 8)
    }
    assert all(score == 7 for article, score, reasons in result)


def test_same_score_orders_newest_first_seen_at_first(make_article):
    older_article = make_article(
        title="Security article from yesterday",
        first_seen_at="2026-10-29T12:00:00Z",
    )
    newer_article = make_article(
        title="Security article from today",
        first_seen_at="2026-10-30T12:00:00Z",
    )
    data = [older_article, newer_article]

    result = scoring("security", data)

    assert len(result) == 2
    assert result[0][1] == result[1][1] == 5
    assert result[0][0] == newer_article
    assert result[1][0] == older_article


def test_sort_score_order_descending(make_article):
    older_article = make_article(
        title="Security article from yesterday",
        first_seen_at="2026-10-29T12:00:00Z",
    )
    newer_article = make_article(
        title="Security article from today",
        first_seen_at="2026-10-30T12:00:00Z",
    )
    newest_article = make_article(
        title="Security article from tomorrow",
        first_seen_at="2026-11-01T12:00:00Z",
    )

    data = [older_article, newer_article, newest_article]

    result = scoring("security", data)

    assert len(result) == 3
    assert result[0][1] == result[1][1] == result[2][1] == 5
    assert result[0][0] == newest_article
    assert result[1][0] == newer_article
    assert result[2][0] == older_article

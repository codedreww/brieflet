import re


def sort_score(matches):
    """
    Sorts matches.

    Args:
        matches: list cointaining [articles, score, reasons]

    Returns:
        sorted matches by descending order on the score and then on the "first_seen" field
    """
    return sorted(
        matches,
        key=lambda match: (
            match[1],
            match[0]["first_seen_at"],
        ),
        reverse=True,
    )


def scoring(keywords, data):
    """
    Scores websites based on keywords inputted by the user.

    Args:
        keywords: words inputted by user.
        data: arcticle found from the database

    Returns:
        Five highest scored arcticle.
    """
    words = set()
    for word in keywords.split(","):
        cleaned = word.strip().lower()
        if cleaned:
            words.add(cleaned)

    matches = []

    for arcticle in data:
        title = (arcticle.get("title") or "").lower().strip()
        description = (arcticle.get("description") or "").lower().strip()
        score = 0
        title_matches = []
        description_matches = []

        for word in words:
            # \b ensures that the word is a whole word. but it fails for words like C++
            # because ++ is a non-word character. to fix, we should use r"(?!\w)" instead
            pattern = r"\b" + re.escape(word) + r"\b"
            if re.search(pattern, title):
                score += 5
                title_matches.append(word)

            if re.search(pattern, description):
                score += 2
                description_matches.append(word)

        if score > 0:
            reasons = []

            if description_matches:
                reasons.append(f"{', '.join(description_matches)} in description")

            if title_matches:
                reasons.append(f"{', '.join(title_matches)} in title")

            formatted_reasons = "; ".join(reasons)
            matches.append([arcticle, score, formatted_reasons])

    sorted_matches = sort_score(matches)
    return sorted_matches[:5]


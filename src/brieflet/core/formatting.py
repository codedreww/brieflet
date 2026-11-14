from datetime import datetime

from brieflet.config import OUTPUT_DIR


def convert_date(stored_date):
    if stored_date:
        parsed_date = datetime.strptime(stored_date, "%Y-%m-%dT%H:%M:%SZ")
        display_date = parsed_date.strftime("%d %b %Y")
    else:
        display_date = "Publication date unavailable"
    return display_date


def format_output_txt(result):
    res = ""
    if not result:
        return "No matching articles found."
    for number, entry in enumerate(result, start=1):
        article = entry[0]["title"]
        source = entry[0]["source"]
        score = entry[1] or "0"
        reason = entry[2]
        description = entry[0].get("description") or "Description unavailable"
        link = entry[0]["link"]

        stored_date = entry[0].get("date")
        display_date = convert_date(stored_date)

        line = f"Article: {article}\nScore: {score} | Source: {source}\nPublished: {display_date}\nLink: {link}\n\nDescription: {description}\nReason: {reason}"
        res += f"{number}.\n{line}\n\n"
    return res


def format_output_md(keywords, result):
    res = ""
    res += "# Research Digest\n\n"
    res += f"Keywords: {keywords}\n"
    res += f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}\n\n"
    res += "## Matching Arcticle: \n"
    if not result:
        res += "No matching articles found."
        return res

    for number, entry in enumerate(result, start=1):
        article = entry[0]["title"]
        source = entry[0]["source"]
        score = entry[1] or "0"
        reason = entry[2]
        description = entry[0].get("description") or "Description unavailable"
        link = entry[0]["link"]

        stored_date = entry[0].get("date")
        display_date = convert_date(stored_date)

        res += f"#### {number}. {article}\n\n"
        res += f"**Score** : {score}\n"
        res += f"**Source** : {source}\n"
        res += f"**Published** : {display_date}\n\n"
        res += f"[Read the arcticle]({link})\n\n"
        res += f"**Description** : {description}\n\n"
        res += f"**Matches** : {reason}\n\n"
    return res


def format_digest_txt(digest):
    """
    Format a stored digest (as returned by get_digest) as plain text.
    """
    header = (
        f"Digest for {digest['digest_date']}\n"
        f"Keywords: {digest['keywords']}\n"
        f"Delivered: {digest['delivered_at'] or 'not yet'}\n"
    )
    if not digest["items"]:
        return header + "\nNo matching articles found."

    lines = [header]
    for item in digest["items"]:
        lines.append(
            f"{item['rank']}. {item['title']}\n"
            f"   Score: {item['score']} | Source: {item['source']} | "
            f"Published: {convert_date(item['date'])}\n"
            f"   Why: {item['reasons']}\n"
            f"   {item['link']}"
        )
    return "\n".join(lines)


def create_markdown(res):
    p = OUTPUT_DIR / "result.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(res, encoding="utf-8")
    return p

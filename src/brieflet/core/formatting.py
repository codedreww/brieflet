from datetime import datetime

from brieflet.config import OUTPUT_DIR


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
        if stored_date:
            parsed_date = datetime.strptime(stored_date, "%Y-%m-%dT%H:%M:%SZ")
            display_date = parsed_date.strftime("%d %b %Y")
        else:
            display_date = "Publication date unavailable"

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
        if stored_date:
            parsed_date = datetime.strptime(stored_date, "%Y-%m-%dT%H:%M:%SZ")
            display_date = parsed_date.strftime("%d %b %Y")
        else:
            display_date = "Publication date unavailable"
        res += f"#### {number}. {article}\n\n"
        res += f"**Score** : {score}\n"
        res += f"**Source** : {source}\n"
        res += f"**Published** : {display_date}\n\n"
        res += f"[Read the arcticle]({link})\n\n"
        res += f"**Description** : {description}\n\n"
        res += f"**Matches** : {reason}\n\n"
    return res


def create_markdown(res):
    p = OUTPUT_DIR / "result.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(res, encoding="utf-8")
    return p

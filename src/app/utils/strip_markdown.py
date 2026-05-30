import re


def strip_markdown(text: str) -> str:
    """
    Remove markdown formatting (bold, italics, inline code, links, etc.) for plain-text search indexing.
    - Removes **bold**, *italic*, __underline__, `code`, [links](url), etc.
    - Leaves plain text and rule IDs intact.
    """
    # Remove bold/italic/underline/code
    text = re.sub(r"(\*\*|__|\*|`)", "", text)
    # Remove markdown links but keep link text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Remove HTML tags (if any remain)
    text = re.sub(r"<[^>]+>", "", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()

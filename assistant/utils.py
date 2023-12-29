import markdown
from bleach import clean


async def convert_markdown_to_html(text):
    """Converts Markdown text to sanitized HTML."""
    html = markdown.markdown(text)
    sanitized_html = clean(html)
    return sanitized_html


# async def convert_newlines_to_br(text):
#     """Convert newline characters in a string to HTML <br> tags."""
#     return text.replace("\n", "<br>")

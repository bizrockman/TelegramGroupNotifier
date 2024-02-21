
def escape_html(text):
    """
    Escapes HTML special characters in the given text.
    """
    if isinstance(text, str):
        return (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            .replace("'", '&#39;'))
    else:
        return text

import re


def prepare_email_message_text(text: str) -> str:
    # Remove spaces around
    text = text.strip()
    # Remove spaces before newlines
    text = re.sub(r"\s*[\n\r]", "\n", text)
    # Leave max two newlines in a row
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def parse_email_subject_and_content(text: str) -> list[str]:
    """
    Email message should contain a subject in the beginning, separated from the content by double newline.
    Returns the list consisted of [subject, content]
    """
    text = prepare_email_message_text(text)
    return text.split('\n\n', 1)


__all__ = [
    prepare_email_message_text,
    parse_email_subject_and_content,
]

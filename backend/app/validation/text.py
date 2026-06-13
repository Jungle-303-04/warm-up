def required_text(value: str, message: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError(message)
    return text

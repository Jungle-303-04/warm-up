from pathlib import PurePosixPath

from app.validation.text import required_text


def relative_path(value: str, empty_message: str, invalid_message: str) -> str:
    path = required_text(value, empty_message)
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or ".." in parsed.parts:
        raise ValueError(invalid_message)
    return path

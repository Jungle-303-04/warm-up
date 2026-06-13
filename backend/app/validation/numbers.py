from typing import TypeVar


Number = TypeVar("Number", int, float)


def min_value(value: Number, minimum: Number, message: str) -> Number:
    if value < minimum:
        raise ValueError(message)
    return value


def between(value: Number, minimum: Number, maximum: Number, message: str) -> Number:
    if not minimum <= value <= maximum:
        raise ValueError(message)
    return value

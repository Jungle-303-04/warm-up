def min_value[Number: (int, float)](value: Number, minimum: Number, message: str) -> Number:
    if value < minimum:
        raise ValueError(message)
    return value


def between[Number: (int, float)](
    value: Number, minimum: Number, maximum: Number, message: str
) -> Number:
    if not minimum <= value <= maximum:
        raise ValueError(message)
    return value

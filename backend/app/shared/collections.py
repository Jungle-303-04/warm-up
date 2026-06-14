def get_list_value[T](values: list[T], index: int, default: T) -> T:
    """외부 API가 병렬 배열을 줄 때 index 누락으로 터지지 않게 기본값을 반환한다."""

    if index >= len(values):
        return default

    return values[index]

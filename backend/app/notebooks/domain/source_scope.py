"""소스/파일 scope 공통 helper."""

from app.notebooks.domain.records import SourceRecord


def select_sources(
    sources: list[SourceRecord],
    source_ids: list[str] | None,
) -> list[SourceRecord]:
    if source_ids is None:
        return sources
    requested = set(source_ids)
    return [source for source in sources if source.id in requested]


def normalize_file_scope(file_paths: list[str] | None) -> set[str] | None:
    if file_paths is None:
        return None
    return {path for path in file_paths if path}


def file_path_in_scope(path: str | None, allowed_paths: set[str] | None) -> bool:
    return allowed_paths is None or path is None or path in allowed_paths

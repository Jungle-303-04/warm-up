from app.pipeline.router import RepoSnapshot
from app.repo_rag.api.schemas import RepoFileChange
from app.repo_rag.domain.identity import file_hash
from app.repo_rag.domain.records import FileRecord


class RepoDiffService:
    def compare(
        self,
        previous_files: dict[str, FileRecord],
        snapshot: RepoSnapshot,
    ) -> list[RepoFileChange]:
        current_hashes = {file.path: file_hash(file) for file in snapshot.files}
        paths = sorted(previous_files.keys() | current_hashes.keys())
        changes: list[RepoFileChange] = []

        for path in paths:
            previous = previous_files.get(path)
            current_hash = current_hashes.get(path)

            if previous is None and current_hash is not None:
                status = "added"
            elif previous is not None and current_hash is None:
                status = "deleted"
            elif previous is not None and previous.content_hash != current_hash:
                status = "modified"
            else:
                status = "unchanged"

            changes.append(
                RepoFileChange(
                    path=path,
                    status=status,
                    previous_hash=previous.content_hash if previous else None,
                    current_hash=current_hash,
                )
            )

        return changes


def change_summary(changes: list[RepoFileChange]) -> str:
    counts = {"added": 0, "modified": 0, "deleted": 0, "unchanged": 0}
    for change in changes:
        counts[change.status] += 1
    return ", ".join(f"{status}={count}" for status, count in counts.items())

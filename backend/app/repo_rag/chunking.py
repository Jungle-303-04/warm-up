from app.repo_rag.identity import file_hash, hash_text
from app.repo_rag.schemas import RepoFileChange
from app.pipeline.schemas import RepoSnapshot, RetrievalChunk


CHUNK_TEXT_LIMIT = 800


class ChunkingService:
    def chunk_changed_files(
        self,
        snapshot: RepoSnapshot,
        changes: list[RepoFileChange],
    ) -> list[RetrievalChunk]:
        changed_paths = {
            change.path for change in changes if change.status in {"added", "modified"}
        }
        chunks: list[RetrievalChunk] = []

        for file in snapshot.files:
            if file.path not in changed_paths:
                continue

            text = file.content.strip()
            if not text:
                continue

            chunk_text = text[:CHUNK_TEXT_LIMIT]
            chunk_hash = hash_text(f"{file.path}\0{file_hash(file)}\0{chunk_text}")[:16]
            chunks.append(
                RetrievalChunk(
                    id=f"{file.path}@{snapshot.commit_sha}:{chunk_hash}",
                    source_path=file.path,
                    text=chunk_text,
                    citation=f"{snapshot.repository}:{file.path}@{snapshot.commit_sha}",
                )
            )

        return chunks

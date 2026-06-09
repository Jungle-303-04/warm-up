from app.schemas.pipeline import CodeReference, RepoSnapshot, RetrievalChunk


class RagIndexService:
    def index(
        self,
        snapshot: RepoSnapshot,
        references: list[CodeReference],
    ) -> list[RetrievalChunk]:
        reference_paths = {reference.path for reference in references}
        chunks: list[RetrievalChunk] = []

        for file in snapshot.files:
            if file.path not in reference_paths:
                continue

            text = file.content.strip()
            if not text:
                continue

            chunks.append(
                RetrievalChunk(
                    id=f"{file.path}@{snapshot.commit_sha}",
                    source_path=file.path,
                    text=text[:800],
                    citation=f"{snapshot.repository}:{file.path}@{snapshot.commit_sha}",
                )
            )

        return chunks

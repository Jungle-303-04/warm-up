from app.pipeline.api.schemas import AgentProposal, PublishSnapshot, RepoSnapshot, RetrievalChunk


class PublishService:
    def publish(
        self,
        snapshot: RepoSnapshot,
        chunks: list[RetrievalChunk],
        proposals: list[AgentProposal],
    ) -> PublishSnapshot:
        safe_name = snapshot.repository.replace("/", "-")

        return PublishSnapshot(
            id=f"publish:{safe_name}:{snapshot.commit_sha}",
            status="published",
            path=f"/published/{safe_name}",
            item_count=len(chunks),
            proposal_count=len(proposals),
        )

from app.schemas.pipeline import AgentProposal, PublishSnapshot, RepoSnapshot, RetrievalChunk


class PublishService:
    def publish(
        self,
        snapshot: RepoSnapshot,
        chunks: list[RetrievalChunk],
        proposals: list[AgentProposal],
    ) -> PublishSnapshot:
        # 실제 정적 파일 생성 전 단계라 지금은 publish 결과 metadata만 만든다.
        safe_name = snapshot.repository.replace("/", "-")

        return PublishSnapshot(
            id=f"publish:{safe_name}:{snapshot.commit_sha}",
            status="published",
            path=f"/published/{safe_name}",
            item_count=len(chunks),
            proposal_count=len(proposals),
        )

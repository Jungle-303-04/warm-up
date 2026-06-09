from hashlib import sha1

from app.schemas.pipeline import PipelineRequest, RepoSnapshot


class RepoSyncService:
    def sync(self, request: PipelineRequest) -> RepoSnapshot:
        # 실제 git clone/fetch 전 단계라 입력 내용을 hash해 안정적인 가짜 commit sha를 만든다.
        digest = sha1()
        digest.update(request.repository.encode())
        digest.update(request.branch.encode())

        for file in request.files:
            digest.update(file.path.encode())
            digest.update(file.content.encode())

        return RepoSnapshot(
            repository=request.repository,
            branch=request.branch,
            commit_sha=digest.hexdigest()[:12],
            files=request.files,
        )

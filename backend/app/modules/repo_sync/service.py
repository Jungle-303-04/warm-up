from hashlib import sha1

from app.schemas import PipelineRequest, RepoSnapshot


class RepoSyncService:
    def sync(self, request: PipelineRequest) -> RepoSnapshot:
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


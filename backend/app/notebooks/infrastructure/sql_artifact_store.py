"""ArtifactStore의 Postgres 구현.

각 연산은 session_scope로 짧은 트랜잭션 경계를 잡는다. add/update는 PK 기준
merge(upsert)로 처리한다. get/update/delete는 notebook_id 불일치 시 KeyError.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.notebooks.domain.artifact_ports import ArtifactStore
from app.notebooks.domain.artifact_records import ArtifactRecord
from app.api.errors import EntityNotFoundError
from app.notebooks.infrastructure.mappers import artifact_to_model, artifact_to_record
from app.notebooks.infrastructure.models import ArtifactModel
from app.repo_rag.infrastructure.db import session_scope


class SqlArtifactStore(ArtifactStore):

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, record: ArtifactRecord) -> None:
        with session_scope(self._session_factory) as session:
            session.merge(artifact_to_model(record))

    def get(self, notebook_id: str, artifact_id: str) -> ArtifactRecord:
        with session_scope(self._session_factory) as session:
            model = session.get(ArtifactModel, artifact_id)
            if model is None or model.notebook_id != notebook_id:
                raise EntityNotFoundError(artifact_id)
            return artifact_to_record(model)

    def list_by_notebook(self, notebook_id: str) -> list[ArtifactRecord]:
        with session_scope(self._session_factory) as session:
            stmt = (
                select(ArtifactModel)
                .where(ArtifactModel.notebook_id == notebook_id)
                .order_by(ArtifactModel.created_at)
            )
            return [artifact_to_record(model) for model in session.scalars(stmt).all()]

    def update(self, record: ArtifactRecord) -> None:
        with session_scope(self._session_factory) as session:
            model = session.get(ArtifactModel, record.id)
            if model is None or model.notebook_id != record.notebook_id:
                raise EntityNotFoundError(record.id)
            session.merge(artifact_to_model(record))

    def delete(self, notebook_id: str, artifact_id: str) -> None:
        with session_scope(self._session_factory) as session:
            model = session.get(ArtifactModel, artifact_id)
            if model is None or model.notebook_id != notebook_id:
                raise EntityNotFoundError(artifact_id)
            session.delete(model)

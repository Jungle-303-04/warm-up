"""반복되는 콜러블 시그니처를 짧고 의미있게 만드는 타입 별칭.

uow_factory: UowFactory          # Callable[[], UnitOfWork]
retriever_factory: RetrieverFactory
"""

from collections.abc import Callable
from typing import Any

from app.repo_rag.application.unit_of_work import UnitOfWork
from app.repo_rag.domain.ports import RepoRagRetriever

# 호출 시 새 UnitOfWork(=트랜잭션 경계)를 만드는 팩토리.
UowFactory = Callable[[], UnitOfWork]

# 세션을 받아 검색 어댑터를 만드는 팩토리(application이 인프라를 직접 import 하지 않도록).
RetrieverFactory = Callable[[Any], RepoRagRetriever]

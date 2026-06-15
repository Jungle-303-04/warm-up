"""인증 Postgres ORM 모델.

GitHub access token을 사용자별로 보관한다. 토큰은 평문으로 저장하므로
운영 환경에서는 컬럼 암호화(예: pgcrypto)나 KMS 적용을 권장한다.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class GitHubTokenModel(Base):
    __tablename__ = "github_tokens"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

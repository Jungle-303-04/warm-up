from sqlalchemy import Column, ForeignKey, Table

from app.core.database import Base

#모르겟음

#이 코드는 페이지와 태그를 연결하는 중간 테이블을 만든 것

# 한 페이지는 여러 태그를 가질 수 있기 때문
# 한 태그는 여러 페이지에 붙을 수 있기 때문
# Page와 Tag는 다대다 관계라서 둘을 직접 연결할 중간 테이블이 필요하다.
# 예: 한 페이지에는 여러 태그가 붙고, 한 태그도 여러 페이지에 붙을 수 있다.
page_tags = Table(
    "page_tags",
    Base.metadata,
    Column(
        "page_id",
        # 연결된 페이지가 삭제되면 page_tags의 연결 정보도 같이 삭제한다.
        ForeignKey("pages.id", ondelete="CASCADE"),
        # page_id + tag_id를 합쳐 기본키로 써서 같은 연결이 중복 저장되지 않게 한다.
        primary_key=True,
    ),
    Column(
        "tag_id",
        # 연결된 태그가 삭제되면 page_tags의 연결 정보도 같이 삭제한다.
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

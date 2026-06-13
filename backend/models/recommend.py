from sqlmodel import SQLModel

class RecommendRequest(SQLModel):
    text: str
    preferred_tone: str | None = None

# 분석결과
class AnalysisResult(SQLModel):
    emotion: str
    visual_traits: list[str]
    writing_style: list[str]
    energy: str
    keywords: list[str]

# 최종 선택 font
class FontSelection(SQLModel):
    font_id: int
    reason: str

# 전체 응답 wrapper
class RecommendResponse(SQLModel):
    analysis: AnalysisResult
    selection: FontSelection
    candidate_fonts: int
    font: dict | None = None


    
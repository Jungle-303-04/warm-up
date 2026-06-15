from pydantic import BaseModel

class RecommendRequest(BaseModel):
    text: str
    preferred_tone: str | None = None

# 분석결과
class AnalysisResult(BaseModel):
    emotion: str
    visual_traits: list[str]
    writing_style: list[str]
    energy: str
    keywords: list[str]

# 최종 선택 font
class FontSelection(BaseModel):
    font_id: int
    reason: str
    display_reason: str

# 전체 응답 wrapper
class RecommendResponse(BaseModel):
    analysis: AnalysisResult
    selection: FontSelection
    candidate_fonts: int
    font: dict | None = None


    
from database import engine
from sqlmodel import Session, select
from models.font import Font
from fastapi import HTTPException

# db에서 fonts 조회
def list_fonts(): 
    try:
        with Session(engine) as session:
            return session.exec(
                select(Font)
            ).all()

    except Exception:
        raise HTTPException(
        status_code=500, 
        detail="폰트 후보 조회중 오류가 발생했습니다.")

# font 후보 정보
def build_candidate_fonts(fonts):
    return [
            {
                "id": font.id,
                "name": font.name,
                "source": font.source,
                "category": font.category,
                "tags": font.tags,
                "description": font.description,
                "weights": font.weights,
                "has_webfont": bool(font.webfonts)
            }        
        for font in fonts
    ]

# 반환 Font(id=2, name="폰트명")
def get_font_by_id(fonts, font_id):
    for font in fonts:
        if font.id == font_id:
            return font

    return None

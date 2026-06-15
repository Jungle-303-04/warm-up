# Third Party
from fastapi import HTTPException
from sqlmodel import Session, select

# Local
from database import engine
from openai_client import client

from models.font import Font
from models.recommend import (RecommendRequest, AnalysisResult, FontSelection, RecommendResponse,
)

from rag.search import search_guides

def run_recommend_agent(request: RecommendRequest):
    text = request.text
    preferred_tone = request.preferred_tone
    fonts, candidate_fonts = get_candidate_fonts()
    analysis_result = analyze_text(text,preferred_tone)
    rag_guides = search_rag_guides(text, analysis_result, preferred_tone)
    rag_context = build_rag_context(rag_guides)
    selection_result = select_font(text, analysis_result, rag_context, candidate_fonts)
    selected_font = find_selected_font(fonts, selection_result)
    selected_font_data = build_selected_font_data(selected_font)
    recommend_response = build_response(analysis_result, selection_result, selected_font_data)

    return recommend_response

def get_candidate_fonts():
    try:
        with Session(engine) as session: fonts = session.exec(select(Font)).all()

    except Exception:
        raise HTTPException(
        status_code=500, 
        detail="폰트 후보 조회중 오류가 발생했습니다.")
    
    if not fonts:
        raise HTTPException(
            status_code=404,
            detail="추천에 사용할 폰트 데이터가 없습니다."
        )
        
    candidate_fonts = [
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

    return fonts, candidate_fonts
    

def analyze_text(text, preferred_tone):
    prompt = f"""
    다음 문장을 폰트 추천에 사용할 수 있도록 분석해줘.

    문장:
    {text}

    선호 톤:
    {preferred_tone}

    반드시 순수 JSON만 반환해.
    마크다운 코드블록을 쓰지 마.
    설명 문장을 쓰지 마.
    JSON 앞뒤에 어떤 문장도 붙이지 마.

    형식:
    {{
    "emotion": "",
    "visual_traits": [],
    "writing_style": [],
    "energy": "",
    "keywords": []
    }}
    """

    analysis_response = client.responses.parse(
            model="gpt-4.1-mini",
            input=prompt,
            text_format=AnalysisResult
        )

    # 응답을 모델로 변환
    analysis_result = analysis_response.output_parsed

    return analysis_result

def search_rag_guides(text, analysis_result, preferred_tone):
    rag_query = f"""
    사용자 문장:
    {text}

    분석 결과:
    emotion={analysis_result.emotion}
    visual_traits={analysis_result.visual_traits}
    writing_style={analysis_result.writing_style}
    energy={analysis_result.energy}
    keywords={analysis_result.keywords}

    선호 톤:
    {preferred_tone}
    """

    rag_guides = search_guides(rag_query, top_k=3)

    return rag_guides

def build_rag_context(rag_guides):
    # GPT가 읽기 좋게 정리한 문자열 버전
    rag_context = "\n\n".join(
        guide["document"]
        for guide in rag_guides
    )

    return rag_context

def select_font(text, analysis_result, rag_context, candidate_fonts):
    selection_prompt = f"""
    사용자 문장:
    {text}

    문장 분석 결과:
    {analysis_result}

    RAG 추천 근거:
    {rag_context}

    후보 폰트:
    {candidate_fonts}

    후보 폰트 중 가장 적합한 폰트 하나를 선택해.
    반드시 후보 목록에 있는 id만 사용해.
        
    추천 이유(reason)는 반드시 아래 내용을 반영해:
    - 문장 분석 결과
    - RAG 추천 근거
    - 후보 폰트의 category, tags, description, weights

    display_reason:
    사용자에게 보여줄 설명을 작성해.

    규칙:
    - 반드시 사용자 글 특징, RAG 근거, 폰트 특징을 모두 포함해 설명해.
    - 단순히 폰트 소개만 하지 마.
    - 왜 이 글에 이 폰트를 추천했는지 설명해.
    - 2~4문장으로 작성해.
    - "~했어요", "~어울려요", "~추천했어요" 말투를 사용해.
    - RAG, 분석 결과, 후보 폰트 등의 단어는 사용하지 마.
    - RAG 추천 근거와 후보 폰트 정보가 충돌하면 후보 폰트 정보를 우선해.
    - 없는 정보를 지어내지 마.

    좋은 예시:
    "강한 감정과 직설적인 표현이 많아 시선을 끌고 힘 있게 보이는 폰트를 추천했어요. 어그로체는 제목용으로 만들어진 꽉 찬 고딕 스타일이라 이런 분위기를 강조하기에 잘 어울려요."
    "차분하고 개인적인 이야기를 담고 있는 글이라 따뜻한 분위기의 폰트를 추천했어요. 메모먼트 꾹꾹체는 손글씨 느낌이 살아 있어 감정을 자연스럽게 전달하기 좋아요."
    "일상적인 생각을 편하게 풀어낸 글이라 읽기 부담이 적은 폰트를 추천했어요. 에스코어드림은 깔끔한 고딕체라 내용이 자연스럽게 읽히도록 도와줘요."

    나쁜 예시:
    "에스코어드림은 가독성이 좋고 깔끔한 폰트예요."
    "어그로체는 제목용으로 적합한 폰트예요."
    "메모먼트 꾹꾹체는 손글씨 폰트예요."
        
    반드시 순수 JSON만 반환해.
    마크다운 코드블록을 쓰지 마.
    설명은 한국어로 답변해.

    형식:
    {{
        "font_id": 0,
        "reason": "",
        "display_reason": ""
    }}
    """
    selection_response = client.responses.parse(
        model="gpt-4.1-mini",
        input=selection_prompt,
        text_format=FontSelection
        )
    
    selection_result = selection_response.output_parsed

    return selection_result

def find_selected_font(fonts, selection_result):
    selected_font = next(
        (
            font
            for font in fonts
            if font.id == selection_result.font_id
        ),
        None
    )
    
    if selected_font is None:
        raise HTTPException(
            status_code=500,
            detail="GPT가 후보 목록에 없는 font_id를 선택했습니다."
        ) 

    return selected_font

def build_selected_font_data(selected_font):
    selected_font_data = {
        "id": selected_font.id,
        "name": selected_font.name,
        "source": selected_font.source,
        "is_paid": selected_font.is_paid,
        "license": selected_font.license,
        "category": selected_font.category,
        "tags": selected_font.tags,
        "description": selected_font.description,
        "weights": selected_font.weights,
        "download_url": selected_font.download_url,
        "source_url": selected_font.source_url,
        "license_summary": selected_font.license_summary,
        "webfonts": selected_font.webfonts,
    }

    return selected_font_data

def build_response(analysis_result, selection_result, selected_font_data):
    recommend_response = RecommendResponse(
    analysis=analysis_result,
    selection=selection_result,
    font=selected_font_data
    )

    return recommend_response


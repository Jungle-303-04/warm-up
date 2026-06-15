from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from database import engine
from models.post import Post
from models.font import Font
from models.user import User
from models.recommend import (RecommendRequest, AnalysisResult, FontSelection, RecommendResponse)

from datetime import datetime, timezone
from openai_client import client
from pydantic import BaseModel
import json
from rag.search import search_guides

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message" : "connected backend"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/posts")
def get_posts():

    with Session(engine) as session:
        # posts 테이블의 모든 row가져오기
        posts = session.exec(select(Post)).all()
        result = []
        for post in posts:

            font = session.get(Font, post.font_id)

            result.append(
                {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "created_at": post.created_at,
                    "font": {
                        "name": font.name,
                        "tags": font.tags
                    } 
                }
            )
        
        return result

@app.post("/posts")
def create_post(post_data : Post):

    if not post_data.title.strip():
        raise HTTPException(status_code=400, detail="title is required")

    if not post_data.content.strip():
        raise HTTPException(status_code=400, detail="content is required")

    # postgreSQL 연결 시작 수행 후 종료
    with Session(engine) as session:
        # 객체 등록 (저장 대기열)
        session.add(post_data)
        # 객체 DB 반영
        session.commit()
        # DB 반영 조회 (최신 상태로 객체 갱신)
        session.refresh(post_data)
        # fast API 자동 json으로 변환해줌
        return post_data

@app.get("/posts/{post_id}")
def get_post(post_id : int): 

    with Session(engine) as session:
        # 해당 id의 Row 가져오기
        post = session.get(Post, post_id)

        if post is None:
            return {"message": "게시글 없음"}
        
        font = session.get(Font, post.font_id)

        return  {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "created_at": post.created_at,
                    "updated_at": post.updated_at,
                    "font": {
                        "name": font.name,
                        "tags": font.tags
                    } 
                }

@app.put("/posts/{post_id}")
def update_post(post_id : int, post_data: Post):

    if not post_data.title.strip():
        raise HTTPException(status_code=400, detail="title is required")

    if not post_data.content.strip():
        raise HTTPException(status_code=400, detail="content is required")
    
    with Session (engine) as session:
        post = session.get(Post, post_id)

        if post is None:
            # FastAPI 제공 예외 클래스로 정확한 상태코드 내려줌
            raise HTTPException(status_code=404, detail="Post not found")

        post.title = post_data.title
        post.content = post_data.content
        post.user_id = post_data.user_id
        post.font_id = post_data.font_id
        post.updated_at = datetime.now(timezone.utc)

        session.add(post)
        session.commit()
        session.refresh(post)

        return {
            "success": True,
            "message": "게시글 수정 완료"
        }


@app.delete("/posts/{post_id}")
def delete_post(post_id : int):
    # 해당 post_id를 db에서 찾아서 있으면 삭제하고 결과반환

    with Session (engine) as session:
        post = session.get(Post, post_id)

        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")

        session.delete(post)
        session.commit()

        return {
            "success": True,
            "message": "게시글 삭제 완료"
        }

@app.post("/recommend", response_model=RecommendResponse)
def recommend_fonts(request: RecommendRequest):
    text = request.text
    preferred_tone = request.preferred_tone

    try:
        with Session(engine) as session: fonts = session.exec(select(Font)).all()

        candidate_fonts = [
                {
                    "id": font.id,
                    "name": font.name,
                    "source": font.source,
                    "category": font.category,
                    "tags": font.tags,
                    "description": font.description,
                    "weights": font.weights,
                    "has_webfont": bool(font.webfonts) > 0
                }        
            for font in fonts
        ]
            
    except Exception as e:
        raise HTTPException(status_code=502, detail="Invalid GPT response format")
    
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

        # 응답 전체
    analysis_response = client.responses.parse(
            model="gpt-4.1-mini",
            input=prompt,
            text_format=AnalysisResult
        )

    # #응답 text 꺼내기
    # analysis_text = response.output_text.strip()
    # #객체 형태의 문자열을 딕셔너리로 변환
    # analysis = json.loads(analysis_text)
    # 응답을 모델로 변환
    analysis_result = analysis_response.output_parsed
    rag_query = f"""
    사용자 문장:
    {text}

    분석 결과:
    emotion={analysis_result.emotion}
    visual_traits={analysis_result.visual_traits}
    writing_style{analysis_result.writing_style}
    energy={analysis_result.energy}
    keywords={analysis_result.keywords}

    선호 톤:
    {preferred_tone}
    """

    rag_guides = search_guides(rag_query, top_k=3)

    selection_prompt = f"""
        사용자 문장:
        {text}

        문장 분석 결과:
        {analysis_result}

        RAG 추천 근거:
        {rag_guides}

        후보 폰트:
        {candidate_fonts}

        후보 폰트 중 가장 적합한 폰트 하나를 선택해.
        반드시 후보 목록에 있는 id만 사용해.
        
        추천 이유(reason)는 반드시 아래 내용을 반영해:
        - 문장 분석 결과
        - RAG 추천 근거
        - 후보 폰트의 category, tags, description, weights

        RAG 추천 근거와 후보 폰트 정보가 충돌하면 후보 폰트 정보를 우선해.
        없는 정보를 지어내지 마.

        반드시 순수 JSON만 반환해.
        마크다운 코드블록을 쓰지 마.
        설명은 한국어로 답변해.

        형식:
        {{
            "font_id": 0,
            "reason": ""
        }}
        """
    selection_response = client.responses.parse(
        model="gpt-4.1-mini",
        input=selection_prompt,
        text_format=FontSelection
        )
    
    # selection_text = selection_response.output_text.strip()
    # selection = json.loads(selection_text)
    selection_result = selection_response.output_parsed

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
    

    # print("선택결과:", selection_result)
    recommend_response = RecommendResponse(
        analysis=analysis_result,
        selection=selection_result,
        candidate_fonts=bool(candidate_fonts),
        font=selected_font_data
    )

    return recommend_response


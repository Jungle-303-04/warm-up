import json
from pathlib import Path

from openai import OpenAI
from rag.builder import build_embedding_inputs
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

# 디렉토리 경로
BASE_DIR = Path(__file__).resolve().parent.parent
GUIDES_PATH = BASE_DIR / "data" / "font_guides.json"
OUTPUT_PATH = BASE_DIR / "data" / "font_guides_embedded.json"

# chunk에 쓰일 문서 open 후 list[dict] 변환
def load_guides() -> list[dict]:
    with open(GUIDES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# 임베딩된 json을 지정 경로에 파일을 쓰고 파이썬 객체를 -> json 파일로 저장
def save_embedded_guides(guides: list[dict])->None:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(guides, f, ensure_ascii=False, indent=2)

# 문서 전체 백터화 수행
def create_embeddings():
    guides = load_guides()
    embedding_inputs = build_embedding_inputs(guides)

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=embedding_inputs,
    )

    # guides, respone를 짝지어서 embedding key에 저장
    for guide, item in zip(guides, response.data):
        guide["embedding"] = item.embedding
    # 저장
    save_embedded_guides(guides)

    # print(f"saved: {OUTPUT_PATH}")

# 사용자 입력문장 embbedding
def embed_query(text:str):

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding

if __name__ == "__main__":
    create_embeddings()
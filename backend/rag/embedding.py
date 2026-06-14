import json
from pathlib import Path

from openai import OpenAI
from rag.builder import build_embedding_inputs
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

BASE_DIR = Path(__file__).resolve().parent.parent
GUIDES_PATH = BASE_DIR / "data" / "font_guides.json"
OUTPUT_PATH = BASE_DIR / "data" / "font_guides_embedded.json"

# chunk에 쓰일 문서 open
def load_guides() -> list[dict]:
    with open(GUIDES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_embedded_guides(guides: list[dict])->None:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(guides, f, ensure_ascii=False, indent=2)

def create_embeddings():
    guides = load_guides()
    embedding_inputs = build_embedding_inputs(guides)

    # print("chunk count", len(guides))
    # print("input count", len(embedding_inputs))
    # print("first input preview:")
    # print(embedding_inputs[0])

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=embedding_inputs,
    )

    for guide, item in zip(guides, response.data):
        guide["embedding"] = item.embedding

    save_embedded_guides(guides)

    # print(f"saved: {OUTPUT_PATH}")

def embed_query(text:str):

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text

    )

    return response.data[0].embedding

if __name__ == "__main__":
    create_embeddings()
# 임베딩에 넣을 텍스트
def build_embedding_text(chunk: dict) -> str:
    return f"""
    제목:
    {chunk['title']}

    내용:
    {chunk['content']}

    태그:
    {"\n".join(chunk.get('tags', []))}

    적용 대상:
    {"\n".join(chunk.get('applies_to', []))}

    추천 카테고리:
    {"\n".join(chunk.get('recommended_categories', []))}

    톤:
    {"\n".join(chunk.get('tone', []))}
    """.strip()

# chunk 여러개를 문자열 여러개로 생성
def build_embedding_inputs(chunks):
    embedding_inputs = []

    for chunk in chunks:
        text = build_embedding_text(chunk)
        embedding_inputs.append(text)
    
    return embedding_inputs
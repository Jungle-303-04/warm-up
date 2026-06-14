# 임베딩에 넣을 텍스트
def build_embedding_text(chunk: dict) -> str:
    return f"""
    제목:
    {chunk['title']}

    내용:
    {chunk['content']}

    태그:
    {chr(10).join(chunk.get('tags', []))}

    적용 대상:
    {chr(10).join(chunk.get('applies_to', []))}

    추천 카테고리:
    {chr(10).join(chunk.get('recommended_categories', []))}

    톤:
    {chr(10).join(chunk.get('tone', []))}
    """.strip()

def build_embedding_inputs(chunks):
    embedding_inputs = []

    for chunk in chunks:
        text = build_embedding_text(chunk)
        embedding_inputs.append(text)

    print(embedding_inputs[0])
    print(embedding_inputs[1])
    print(len(embedding_inputs[1]))
    
    return embedding_inputs
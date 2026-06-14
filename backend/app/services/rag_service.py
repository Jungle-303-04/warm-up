from app.models.page import Page


def block_to_text(block) -> str:
    """
    page_blocks 한 개를 RAG용 텍스트 한 줄로 바꾼다.
    """

    block_type = block.type.value if hasattr(block.type, "value") else str(block.type)
    content = (block.content or "").strip()

    if not content:
        return ""

    if block_type == "HEADING":
        return f"## {content}"

    if block_type == "BULLET":
        return f"- {content}"

    if block_type == "CHECKLIST":
        checked = getattr(block, "checked", False)
        status = "완료" if checked else "미완료"
        return f"- [{status}] {content}"

    if block_type == "CODE":
        return f"```code\n{content}\n```"

    return content

def build_page_header(page: Page) -> str:
    """
    chunk마다 앞에 붙일 메타 정보.
    이 chunk가 어떤 회의/회고에서 나온 내용인지 알려준다.
    """

    tag_names = ", ".join(tag.name for tag in page.tags) if page.tags else "없음"
    page_type = page.type.value if hasattr(page.type, "value") else str(page.type)

    return (
        f"제목: {page.title}\n"
        f"날짜: {page.date}\n"
        f"종류: {page_type}\n"
        f"태그: {tag_names}\n\n"
    )

def build_page_chunks(page: Page, max_chars: int = 1200) -> list[str]:
    """
    Page 하나를 RAG 검색용 chunk 여러 개로 나눈다.

    기준:
    1. 제목/날짜/태그 header를 모든 chunk에 붙인다.
    2. page_blocks를 order_index 순서대로 합친다.
    3. max_chars를 넘으면 새 chunk로 나눈다.
    """

    header = build_page_header(page)
    chunk_prefix = header + "내용:\n"

    chunks: list[str] = []
    current_chunk = chunk_prefix

    sorted_blocks = sorted(page.blocks, key=lambda block: block.order_index)

    for block in sorted_blocks:
        block_text = block_to_text(block)

        if not block_text:
            continue

        piece = block_text + "\n\n"

        # 현재 chunk에 이 block을 붙이면 너무 길어지는 경우
        if len(current_chunk) + len(piece) > max_chars and current_chunk != chunk_prefix:
            chunks.append(current_chunk.strip())

            # 새 chunk에도 header를 다시 붙인다.
            current_chunk = chunk_prefix + piece
        else:
            current_chunk += piece

    # 마지막 chunk 저장
    if current_chunk.strip() != chunk_prefix.strip():
        chunks.append(current_chunk.strip())

    return chunks
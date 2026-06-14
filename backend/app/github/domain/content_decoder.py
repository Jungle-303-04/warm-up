import base64
import binascii

from app.github.api.schema import GitHubFileResponseDTO


BASE64_ENCODING = "base64"
DEFAULT_TEXT_ENCODING = "utf-8"
PLAIN_TEXT_ENCODINGS = {DEFAULT_TEXT_ENCODING, "text"}


class GitHubContentDecoder:
    """GitHub Contents API의 encoding 값을 보고 파일 본문을 UTF-8 텍스트로 복원한다."""

    def decode(self, file_response: GitHubFileResponseDTO) -> str:
        """RAG MVP가 읽을 수 있는 base64, utf-8, text 응답만 명확히 허용한다."""

        encoding = file_response.encoding

        if encoding in PLAIN_TEXT_ENCODINGS:
            return file_response.content

        if encoding == BASE64_ENCODING:
            return self.decode_base64_text(file_response.content)

        raise ValueError(f"unsupported github file encoding: {encoding}")

    def decode_base64_text(self, content: str) -> str:
        """GitHub가 내려준 base64 파일 본문을 실제 코드/문서 문자열로 바꾼다."""

        try:
            return base64.b64decode(compact_base64_text(content)).decode(
                DEFAULT_TEXT_ENCODING
            )
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise ValueError("file_response.content must be valid utf-8 base64") from exc


def compact_base64_text(content: str) -> str:
    """줄바꿈이 섞인 base64 문자열을 디코딩 가능한 연속 문자열로 만든다."""

    return "".join(content.split())

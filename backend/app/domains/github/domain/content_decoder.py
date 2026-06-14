import base64
import binascii

from app.domains.github.api.schema import GitHubFileResponseDTO


BASE64_ENCODING = "base64"
DEFAULT_TEXT_ENCODING = "utf-8"
PLAIN_TEXT_ENCODINGS = {DEFAULT_TEXT_ENCODING, "text"}


class GitHubContentDecoder:
    def decode(self, file_response: GitHubFileResponseDTO) -> str:
        encoding = file_response.encoding

        if encoding in PLAIN_TEXT_ENCODINGS:
            return file_response.content

        if encoding == BASE64_ENCODING:
            return self.decode_base64_text(file_response.content)

        raise ValueError(f"unsupported github file encoding: {encoding}")

    def decode_base64_text(self, content: str) -> str:
        try:
            return base64.b64decode(compact_base64_text(content)).decode(
                DEFAULT_TEXT_ENCODING
            )
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise ValueError("file_response.content must be valid utf-8 base64") from exc


def compact_base64_text(content: str) -> str:
    return "".join(content.split())

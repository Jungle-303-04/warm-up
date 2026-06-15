import json

from mcp.server.fastmcp import FastMCP

from font_mcp.font_tools import (
    list_fonts,
    build_candidate_fonts,
    get_font_by_id,
    build_font_detail,
)

mcp = FastMCP("font-recommendation-server")

@mcp.tool()
def list_candidate_fonts() -> str:
    fonts = list_fonts()
    candidate_fonts = build_candidate_fonts(fonts)

    return json.dumps(candidate_fonts, ensure_ascii=False)

@mcp.tool()
def get_font_detail_by_id(font_id: int) -> str:
    fonts = list_fonts()
    font = get_font_by_id(fonts, font_id)

    if font is None:
        return json.dumps(None, ensure_ascii=False)

    return json.dumps(build_font_detail(font), ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
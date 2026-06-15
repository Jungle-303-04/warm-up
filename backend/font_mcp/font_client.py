import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def call_font_tool(
    tool_name: str,
    arguments: dict | None = None,
):
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "font_mcp.font_server"],
    )

    async with stdio_client(server_params) as (
        read,
        write,
    ):
        async with ClientSession(
            read,
            write,
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments or {},
            )

            return result


def list_candidate_fonts_from_mcp():
    result = asyncio.run(
        call_font_tool(
            "list_candidate_fonts"
        )
    )

    return json.loads(
        result.content[0].text
    )


def get_font_detail_by_id_from_mcp(
    font_id: int,
):
    result = asyncio.run(
        call_font_tool(
            "get_font_detail_by_id",
            {
                "font_id": font_id
            }
        )
    )

    return json.loads(
        result.content[0].text
    )
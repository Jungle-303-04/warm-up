import logging
import sys
from typing import Any

from langchain_core.tools import StructuredTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import Field, create_model

_LOGGER = logging.getLogger(__name__)


class MCPClient:
    def __init__(self, server_path: str = "app.mcp.server"):
        # stdio 기반으로 python -m app.mcp.server 프로세스를 띄우는 설정
        # sys.executable 사용으로 가상환경(venv) python 바이너리 지정
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", server_path],
        )

    async def list_tools_as_langchain(self) -> list[StructuredTool]:
        """Fetch tools from MCP server and convert them to LangChain StructuredTool objects."""
        try:
            async with stdio_client(self.server_params) as (read, write), \
                   ClientSession(read, write) as session:
                await session.initialize()
                mcp_tools = await session.list_tools()

                lc_tools = []
                for tool in mcp_tools.tools:
                    lc_tools.append(self._to_langchain_tool(tool))
                return lc_tools
        except Exception as exc:
            _LOGGER.warning("MCP 서버 도구 목록 조회 실패", extra={"error": str(exc)})
            return []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call a specific tool on the MCP server and return its string result."""
        try:
            async with stdio_client(self.server_params) as (read, write), \
                   ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)

                # content 결과 파싱 및 머징
                texts = []
                for content in result.content:
                    text = getattr(content, "text", None)
                    if isinstance(text, str):
                        texts.append(text)
                    elif isinstance(content, dict) and "text" in content:
                        texts.append(str(content["text"]))
                return "\n".join(texts)
        except Exception as e:
            return f"Error executing tool '{tool_name}' on MCP server: {e!s}"

    def _to_langchain_tool(self, mcp_tool) -> StructuredTool:
        # JSON Schema -> Pydantic Model 동적 변환.
        # inputSchema는 보통 dict(JSON Schema)지만,
        # 드물게 Pydantic 모델로 올 수 있어 dict로 정규화함
        schema_dict = mcp_tool.inputSchema
        if not isinstance(schema_dict, dict):
            if hasattr(schema_dict, "model_dump"):
                schema_dict = schema_dict.model_dump()
            elif hasattr(schema_dict, "__dict__"):
                schema_dict = dict(schema_dict.__dict__)
            else:
                schema_dict = {}

        args_schema = _json_schema_to_pydantic(mcp_tool.name, schema_dict)
        name = mcp_tool.name
        description = mcp_tool.description

        # 비동기 함수 프록시 정의
        async def _tool_func(**kwargs):
            return await self.call_tool(name, kwargs)

        return StructuredTool(
            name=name,
            description=description,
            func=None,
            coroutine=_tool_func,
            args_schema=args_schema
        )


def _json_schema_to_pydantic(name: str, schema: dict) -> Any:
    """Convert standard JSON Schema to a dynamic Pydantic model for LangChain integration."""
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    fields = {}
    for prop_name, prop_info in properties.items():
        prop_type = Any
        t = prop_info.get("type")
        if t == "string":
            prop_type = str
        elif t == "integer":
            prop_type = int
        elif t == "number":
            prop_type = float
        elif t == "boolean":
            prop_type = bool
        elif t == "array":
            prop_type = list
        elif t == "object":
            prop_type = dict
            
        desc = prop_info.get("description", "")
        # 필수 인자면 default = ... (Required), 아니면 None
        default = ... if prop_name in required else None
        fields[prop_name] = (prop_type, Field(default=default, description=desc))
        
    return create_model(f"{name}Schema", **fields)

import asyncio
from typing import Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import StructuredTool
from pydantic import create_model, Field

class MCPClient:
    def __init__(self, server_path: str = "app.mcp.server"):
        # stdio 기반으로 python -m app.mcp.server 프로세스를 띄우는 설정
        # sys.executable을 쓰면 가상환경(venv) 내의 python 바이너리가 정확히 지정됩니다.
        import sys
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", server_path],
        )

    async def list_tools_as_langchain(self) -> List[StructuredTool]:
        """Fetch tools from MCP server and convert them to LangChain StructuredTool objects."""
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    mcp_tools = await session.list_tools()
                    
                    lc_tools = []
                    for tool in mcp_tools.tools:
                        lc_tools.append(self._to_langchain_tool(tool))
                    return lc_tools
        except Exception as e:
            print(f"Error fetching tools from MCP Server: {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call a specific tool on the MCP server and return its string result."""
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    
                    # content 결과 파싱 및 머징
                    texts = []
                    for content in result.content:
                        if hasattr(content, "text"):
                            texts.append(content.text)
                        elif isinstance(content, dict) and "text" in content:
                            texts.append(content["text"])
                    return "\n".join(texts)
        except Exception as e:
            return f"Error executing tool '{tool_name}' on MCP server: {str(e)}"

    def _to_langchain_tool(self, mcp_tool) -> StructuredTool:
        # JSON Schema -> Pydantic Model 동적 변환
        schema_dict = mcp_tool.inputSchema
        if isinstance(schema_dict, hasattr(schema_dict, "dict") and schema_dict.__class__ or dict):
            # inputSchema가 Pydantic 모델인 경우 dict로 변환
            if not isinstance(schema_dict, dict):
                schema_dict = schema_dict.model_dump() if hasattr(schema_dict, "model_dump") else schema_dict.__dict__
        
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

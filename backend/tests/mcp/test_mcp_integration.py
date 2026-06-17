
import pytest

from app.mcp.client import MCPClient


@pytest.mark.asyncio
async def test_mcp_client_list_tools() -> None:
    client = MCPClient()
    tools = await client.list_tools_as_langchain()
    
    # FastMCP 서버에 등록된 2개의 도구가 잘 조회되는지 검증
    assert len(tools) >= 2
    tool_names = [tool.name for tool in tools]
    assert "get_weather_forecast" in tool_names
    assert "search_github_repositories" in tool_names


@pytest.mark.asyncio
async def test_mcp_client_call_weather_tool() -> None:
    client = MCPClient()
    
    # Seoul 날씨 조회 도구 호출 검증
    result = await client.call_tool("get_weather_forecast", {"city": "Seoul"})
    assert "Seoul: 24°C, Sunny" in result
    
    # 런던 날씨 조회 도구 호출 검증
    result_london = await client.call_tool("get_weather_forecast", {"city": "London"})
    assert "London: 18°C, Light Rain" in result_london


@pytest.mark.asyncio
async def test_mcp_client_call_github_tool_unauthorized() -> None:
    # GITHUB_TOKEN이 세팅되어 있지 않거나 임의값일 때의 호출 검증
    client = MCPClient()
    
    # 비어있는 검색어나 일반 검색어로 API 호출 시도
    result = await client.call_tool("search_github_repositories", {"query": "langchain"})
    
    # API 호출이 에러 없이 메시지를 반환했거나 403 Forbidden(Rate Limit) 등 예외 메시지가 잘 파싱되었는지 검증
    assert isinstance(result, str)
    assert len(result) > 0

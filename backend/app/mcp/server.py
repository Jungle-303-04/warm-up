import os
import httpx
from mcp.server.fastmcp import FastMCP

# MCP 서버 초기화
mcp = FastMCP("SystemMCP")

@mcp.tool()
async def get_weather_forecast(city: str) -> str:
    """Get the weather forecast for a given city.
    
    Args:
        city: The name of the city (e.g. "Seoul", "Tokyo", "London").
    """
    city_lower = city.strip().lower()
    if "seoul" in city_lower:
        return "Seoul: 24°C, Sunny, Humidity 45%, Wind 5km/h."
    elif "tokyo" in city_lower:
        return "Tokyo: 26°C, Partly Cloudy, Humidity 50%, Wind 7km/h."
    elif "london" in city_lower:
        return "London: 18°C, Light Rain, Humidity 80%, Wind 12km/h."
    else:
        return f"{city}: 20°C, Clear Sky, Humidity 55%, Wind 8km/h. (Mocked)"

@mcp.tool()
async def search_github_repositories(query: str) -> str:
    """Search public GitHub repositories by query string.
    
    Args:
        query: The search query (e.g. "langchain python", "fastapi react").
    """
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "RepoLM-MCP-Server/1.0"
    }
    if token:
        headers["Authorization"] = f"token {token}"
        
    url = f"https://api.github.com/search/repositories?q={query}&per_page=3"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 401:
                return "Error: Unauthorized. The provided GITHUB_TOKEN is invalid."
            elif response.status_code == 403:
                return "Error: Rate limit exceeded or forbidden. Try setting a GITHUB_TOKEN to increase limits."
            elif response.status_code != 200:
                return f"Error: GitHub API returned status code {response.status_code} with detail: {response.text}"
                
            data = response.json()
            items = data.get("items", [])
            if not items:
                return f"No GitHub repositories found for query: '{query}'"
                
            results = []
            for item in items:
                # 민감 정보 차단을 위해 필요한 정보만 필터링하여 프롬프트 정제 데이터로 반환
                results.append(
                    f"Name: {item.get('full_name')}\n"
                    f"Description: {item.get('description') or 'No description'}\n"
                    f"Stars: {item.get('stargazers_count')}\n"
                    f"URL: {item.get('html_url')}"
                )
            return "\n---\n".join(results)
    except Exception as e:
        return f"Error occurred during GitHub search: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")

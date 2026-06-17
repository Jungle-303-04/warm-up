from dataclasses import dataclass
from typing import Any, Callable


TOOL_LIST_REPOSITORIES = "list_repositories"
TOOL_LIST_BRANCHES = "list_branches"
TOOL_SEARCH_REPOSITORY_TARGETS = "search_repository_targets"
TOOL_SHOW_BASIS = "show_basis"
TOOL_LIST_FILES = "list_files"
TOOL_CHANGE_BASIS = "change_basis"
TOOL_RESOLVE_RAG_BASIS = "resolve_rag_basis"
TOOL_RETRIEVE_RAG = "retrieve_rag"
TOOL_COMPARE_SNAPSHOTS = "compare_snapshots"
TOOL_GENERAL_CHAT = "general_chat"
TOOL_CLARIFY = "clarify"


AgentToolHandler = Callable[[Any], dict[str, Any]]


@dataclass(frozen=True)
class AgentTool:
    """에이전트가 실행할 수 있는 행동 하나와 실제 실행 함수를 묶는다."""

    name: str
    description: str
    handler: AgentToolHandler


class AgentToolRegistry:
    """LangGraph가 tool name만으로 실제 행동을 실행하게 해주는 도구 목록."""

    def __init__(self, tools: list[AgentTool]) -> None:
        self.tools = {tool.name: tool for tool in tools}

    def run(self, name: str, state: Any) -> dict[str, Any]:
        """선택된 tool을 실행하고, 모르는 tool이면 사용자에게 명확히 되묻는다."""

        tool = self.tools.get(name)
        if tool is None:
            return {
                "final_answer": f"실행할 수 없는 도구입니다: {name}",
                "repository_basis_changed": False,
            }
        return tool.handler(state)

    def describe(self) -> list[str]:
        """디버깅과 문서화를 위해 등록된 tool 이름과 설명을 문자열로 돌려준다."""

        return [
            f"{tool.name}: {tool.description}"
            for tool in self.tools.values()
        ]

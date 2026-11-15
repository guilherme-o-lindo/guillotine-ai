"""Real MCP stdio + simulated PydanticAI model + LangGraph + permission checks.

No live LLM, 9Router, external network, or production database is required.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from mcp import StdioServerParameters
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from guillotine.core.agent import create_agent
from guillotine.core.approvals import (
    ApprovalChoice,
    ApprovalManager,
    ApprovalRequest,
    JsonValue,
)
from guillotine.core.graph import build_workflow
from guillotine.core.permissions import (
    PermissionDecision,
    PermissionManager,
    PermissionProfile,
    PermissionRule,
)
from guillotine.memory.manager import MemoryManager
from guillotine.memory.storage import database
from guillotine.services.conversations import ConversationService
from guillotine.tools.core.contracts import ToolEffect, ToolSecurity
from guillotine.tools.core.executor import ToolExecutor
from guillotine.tools.core.registry import ToolRegistry
from guillotine.tools.mcp.client import MCPClient, stdio_session_factory
from guillotine.tools.mcp.manager import MCPManager

TOOL_ID = "mcp:fixture:write_marker"
SERVER_FILE = Path(__file__).with_name("stdio_server.py")
WRITE_SECURITY = ToolSecurity(effects=frozenset({ToolEffect.WRITE}))


def marker_resource(arguments: Mapping[str, JsonValue]) -> str:
    """Resolve the resource from real arguments, not an LLM-declared scope."""
    path = arguments.get("path")
    if not isinstance(path, str) or not path:
        raise ValueError("A nonempty path is required")
    return Path(path).resolve().as_uri()


def simulated_model(marker: Path) -> FunctionModel:
    """Deterministically call the PydanticAI gateway, then return its result."""
    arguments = json.dumps(
        {"path": str(marker), "content": "WRITTEN VIA PYDANTICAI"},
        ensure_ascii=False,
    )

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        del info
        returns = [
            part
            for message in messages
            if isinstance(message, ModelRequest)
            for part in message.parts
            if isinstance(part, ToolReturnPart)
        ]
        if returns:
            return ModelResponse(
                parts=[
                    TextPart(content=f"Resultado da ferramenta: {returns[-1].content}")
                ]
            )
        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name="guillotine_execute_tool",
                    args={"tool_id": TOOL_ID, "arguments_json": arguments},
                )
            ]
        )

    return FunctionModel(respond)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("decision", "approval_choice", "expected_write"),
    [
        pytest.param(PermissionDecision.ALLOW, None, True, id="explicit-allow"),
        pytest.param(PermissionDecision.DENY, None, False, id="explicit-deny"),
        pytest.param(
            PermissionDecision.REQUIRE_APPROVAL,
            ApprovalChoice.APPROVE_ONCE,
            True,
            id="approval-granted",
        ),
        pytest.param(
            PermissionDecision.REQUIRE_APPROVAL,
            ApprovalChoice.DENY,
            False,
            id="approval-refused",
        ),
    ],
)
async def test_model_to_graph_to_authorized_real_mcp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    decision: PermissionDecision,
    approval_choice: ApprovalChoice | None,
    expected_write: bool,
) -> None:
    """A simulated model's tool call must traverse the production guards."""
    # MemoryManager's SQLite helper reads this module attribute at runtime.
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "conversations.sqlite3")
    memory = MemoryManager()
    await memory.initialize()

    marker = tmp_path / "marker.txt"
    resource_id = marker.resolve().as_uri()
    registry = ToolRegistry()
    prompts: list[ApprovalRequest] = []

    async def current_permissions() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(PermissionRule(TOOL_ID, resource_id, decision),),
        )

    async def prompt(request: ApprovalRequest) -> ApprovalChoice:
        prompts.append(request)
        assert request.tool_id == TOOL_ID
        assert request.resource_id == resource_id
        assert approval_choice is not None
        return approval_choice

    executor = ToolExecutor(
        registry,
        current_permissions,
        approvals=ApprovalManager(prompt),
    )
    manager = MCPManager(registry, executor)
    client = MCPClient(
        stdio_session_factory(
            StdioServerParameters(command=sys.executable, args=[str(SERVER_FILE)])
        )
    )

    try:
        registration = await manager.connect(
            "fixture",
            client,
            resolvers={"write_marker": marker_resource},
            security={"write_marker": WRITE_SECURITY},
        )
        assert registration.tool_ids == (TOOL_ID,)
        assert len(registry.list_tools()) == 1

        agent = create_agent(
            simulated_model(marker),
            registry=registry,
            executor=executor,
        )
        async with AsyncSqliteSaver.from_conn_string(
            str(tmp_path / "checkpoints.sqlite3")
        ) as checkpointer:
            await checkpointer.setup()
            workflow = build_workflow(memory, checkpointer, agent)
            service = ConversationService(memory, workflow, checkpointer)
            conversation_id = await service.create("End-to-end MCP")

            reply = await service.send_message(
                conversation_id, "Use a ferramenta para gravar o marcador."
            )
            history = await service.get_history(conversation_id)

        assert "Resultado da ferramenta:" in reply
        assert len(history) == 2
        assert history[-1]["content"] == reply
        assert marker.exists() is expected_write
        if expected_write:
            assert marker.read_text(encoding="utf-8") == "WRITTEN VIA PYDANTICAI"
            assert "marker written" in reply
        else:
            assert "não autorizada" in reply

        assert len(prompts) == (
            1 if decision is PermissionDecision.REQUIRE_APPROVAL else 0
        )
    finally:
        await manager.close()

    assert manager.list_servers() == ()
    assert registry.list_tools() == ()


# Keep the public-web flow in the existing end-to-end test module. The real MCP
# session is disposable; the HTTP transport is stubbed to avoid internet access.
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("search_approval", "fetch_approval", "expected_fetches"),
    [
        pytest.param(ApprovalChoice.DENY, None, 0, id="search-refused"),
        pytest.param(
            ApprovalChoice.APPROVE_ONCE,
            ApprovalChoice.DENY,
            0,
            id="fetch-refused",
        ),
        pytest.param(
            ApprovalChoice.APPROVE_ONCE,
            ApprovalChoice.APPROVE_ONCE,
            1,
            id="both-approved",
        ),
    ],
)
async def test_search_then_safe_fetch_requires_separate_approvals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    search_approval: ApprovalChoice,
    fetch_approval: ApprovalChoice | None,
    expected_fetches: int,
) -> None:
    """Real MCP search -> PydanticAI gateway -> guarded local fetch -> source."""
    from guillotine.core.mcp_configuration import (
        QueryResource,
        URLResource,
        resource_resolver,
    )
    from guillotine.tools.local import web_fetch as local_safe_fetch
    from guillotine.tools.local.safe_fetch import FetchResult

    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "conversations.sqlite3")
    memory = MemoryManager()
    await memory.initialize()

    search_id = "mcp:search_fixture:search"
    fetch_id = local_safe_fetch.TOOL_ID
    query = "documentação MCP"
    url = "https://example.org/docs/mcp"
    final_url = "https://example.org/docs/mcp/final"
    search_resolver = resource_resolver(QueryResource(kind="query", argument="query"))
    url_resolver = resource_resolver(URLResource(kind="url", argument="url"))
    search_scope = search_resolver({"query": query})
    fetch_scope = url_resolver({"url": url})
    assert search_scope is not None and fetch_scope is not None

    registry = ToolRegistry()
    requested: list[str] = []
    network_calls: list[str] = []

    def fake_fetch_public_page(page_url: str, **_kwargs: object) -> FetchResult:
        network_calls.append(page_url)
        return FetchResult(
            url=final_url,
            status=200,
            content_type="text/html",
            text="EVIDENCIA_DOCUMENTAL_MCP",
        )

    monkeypatch.setattr(local_safe_fetch, "fetch_public_page", fake_fetch_public_page)

    async def current_permissions() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(
                PermissionRule(
                    search_id, search_scope, PermissionDecision.REQUIRE_APPROVAL
                ),
                PermissionRule(
                    fetch_id, fetch_scope, PermissionDecision.REQUIRE_APPROVAL
                ),
            ),
        )

    async def prompt(request: ApprovalRequest) -> ApprovalChoice:
        requested.append(request.tool_id)
        # No outbound HTTP request may occur before fetch's approval.
        assert not network_calls
        if request.tool_id == search_id:
            assert request.resource_id == search_scope
            return search_approval
        assert request.tool_id == fetch_id
        assert request.resource_id == fetch_scope
        assert fetch_approval is not None
        return fetch_approval

    executor = ToolExecutor(
        registry,
        current_permissions,
        approvals=ApprovalManager(prompt),
    )
    manager = MCPManager(registry, executor)
    local_safe_fetch.register_safe_fetch(registry, executor)

    fixture_file = Path(__file__).with_name("search_fixture_server.py")
    client = MCPClient(
        stdio_session_factory(
            StdioServerParameters(command=sys.executable, args=[str(fixture_file)])
        )
    )

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        del info
        returns = [
            part
            for message in messages
            if isinstance(message, ModelRequest)
            for part in message.parts
            if isinstance(part, ToolReturnPart)
        ]
        if not returns:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="guillotine_execute_tool",
                        args={
                            "tool_id": search_id,
                            "arguments_json": json.dumps({"query": query}),
                        },
                    )
                ]
            )
        if len(returns) == 1:
            search_result = str(returns[0].content)
            if "não autorizada" in search_result:
                return ModelResponse(parts=[TextPart(content="Pesquisa recusada")])
            if url not in search_result:
                return ModelResponse(
                    parts=[TextPart(content="Resultado sem fonte válida")]
                )
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="guillotine_execute_tool",
                        args={
                            "tool_id": fetch_id,
                            "arguments_json": json.dumps({"url": url}),
                        },
                    )
                ]
            )
        fetch_result = str(returns[-1].content)
        if final_url in fetch_result and "EVIDENCIA_DOCUMENTAL_MCP" in fetch_result:
            return ModelResponse(
                parts=[
                    TextPart(content=f"Fonte: {final_url} | EVIDENCIA_DOCUMENTAL_MCP")
                ]
            )
        return ModelResponse(parts=[TextPart(content="Leitura recusada")])

    try:
        registration = await manager.connect(
            "search_fixture",
            client,
            resolvers={"search": search_resolver},
            security={
                "search": ToolSecurity(
                    effects=frozenset({ToolEffect.READ, ToolEffect.NETWORK})
                )
            },
        )
        assert registration.tool_ids == (search_id,)
        assert {entry.identifier for entry in registry.list_tools()} == {
            search_id,
            fetch_id,
        }

        agent = create_agent(
            FunctionModel(respond), registry=registry, executor=executor
        )
        async with AsyncSqliteSaver.from_conn_string(
            str(tmp_path / "checkpoints.sqlite3")
        ) as checkpointer:
            await checkpointer.setup()
            workflow = build_workflow(memory, checkpointer, agent)
            service = ConversationService(memory, workflow, checkpointer)
            conversation_id = await service.create("End-to-end web research")
            reply = await service.send_message(
                conversation_id, "Pesquise a documentação e cite a página que leu."
            )
            history = await service.get_history(conversation_id)

        assert len(history) == 2
        assert history[-1]["content"] == reply
        assert network_calls == ([url] if expected_fetches else [])
        if search_approval is ApprovalChoice.DENY:
            assert requested == [search_id]
            assert reply == "Pesquisa recusada"
        else:
            assert requested == [search_id, fetch_id]
            if fetch_approval is ApprovalChoice.DENY:
                assert reply == "Leitura recusada"
            else:
                assert reply == f"Fonte: {final_url} | EVIDENCIA_DOCUMENTAL_MCP"
    finally:
        await manager.close()

    assert manager.list_servers() == ()
    assert {entry.identifier for entry in registry.list_tools()} == {fetch_id}

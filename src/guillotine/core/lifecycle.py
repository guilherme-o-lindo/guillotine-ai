"""Application startup and cleanup, including guarded tool infrastructure."""

from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from guillotine.core.agent import create_agent
from guillotine.core.approvals import ApprovalManager
from guillotine.core.checkpoint import get_checkpointer
from guillotine.core.graph import build_workflow
from guillotine.core.permission_store import PermissionStore
from guillotine.core.permissions import PermissionManager
from guillotine.core.tool_audit import ToolAuditStore
from guillotine.interfaces.approval_prompt import terminal_approval_prompt
from guillotine.memory.manager import MemoryManager
from guillotine.models.provider import model_lifecycle
from guillotine.models.router import router_lifecycle
from guillotine.services.conversations import ConversationService
from guillotine.tools.core.executor import ToolExecutor
from guillotine.tools.core.registry import ToolRegistry
from guillotine.tools.local.web_fetch import register_safe_fetch
from guillotine.tools.mcp.manager import MCPManager

# Caller-provided setup MUST be trusted application code, never model output.
type ConfigureTools = Callable[[MCPManager], Awaitable[None]]


@asynccontextmanager
async def lifespan(
    *, configure_tools: ConfigureTools | None = None
) -> AsyncGenerator[ConversationService, None]:
    """Keep legacy CLI behavior unchanged until tools are explicitly configured.

    A trusted startup hook may connect selected MCP tools with resource resolvers.
    Sessions close in the same async task that opened them, after the agent ends.
    """
    async with router_lifecycle(), model_lifecycle() as model:
        memory = MemoryManager()
        await memory.initialize()

        registry = ToolRegistry()
        store = PermissionStore()
        await store.initialize()
        audit = ToolAuditStore()
        await audit.initialize()

        async def current_permissions() -> PermissionManager:
            return (await store.load()).manager(registry)

        executor = ToolExecutor(
            registry,
            current_permissions,
            approvals=ApprovalManager(terminal_approval_prompt),
            audit=audit.record,
        )
        manager = MCPManager(registry, executor)
        register_safe_fetch(registry, executor)
        try:
            if configure_tools is not None:
                await configure_tools(manager)

            agent = create_agent(model, registry=registry, executor=executor)
            async with get_checkpointer() as checkpointer:
                workflow = build_workflow(memory, checkpointer, agent)
                yield ConversationService(memory, workflow, checkpointer)
        finally:
            await manager.close()

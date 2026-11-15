"""Authorization boundary for trusted native-tool dispatch adapters.

Native argument validation and invocation remain with PydanticAI / MCP SDK.
Every executable tool requires a trusted resource resolver and invocation adapter.
This module is not a sandbox and must not be bypassed by direct SDK calls.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import cast

from guillotine.core.approvals import ApprovalManager, JsonValue
from guillotine.core.permissions import (
    PermissionDecision,
    PermissionManager,
    PermissionResult,
)
from guillotine.tools.registry import RegisteredTool, ToolRegistry

# The application wires these to the SDK's existing invocation/validation APIs.
type ToolInvoker = Callable[[dict[str, JsonValue]], Awaitable[object]]
type ResourceResolver = Callable[[Mapping[str, JsonValue]], str | None]
type CurrentPermissions = Callable[[], Awaitable[PermissionManager]]


class ToolExecutionDenied(PermissionError):
    """Execution is not authorized (including an unapproved request)."""


class ToolAdapterMissing(LookupError):
    """No trusted adapter is bound to this registered tool."""


@dataclass(frozen=True, slots=True)
class _Adapter:
    registration: RegisteredTool
    invoke: ToolInvoker
    resource: ResourceResolver


class ToolExecutor:
    """Authorize each call before dispatching to an injected native SDK adapter.

    The permission provider must load CURRENT policy on every invocation; it
    can read PermissionStore.manager(registry) or use another trusted source.
    A recheck after human approval handles policy changes during the prompt.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        current_permissions: CurrentPermissions,
        *,
        approvals: ApprovalManager | None = None,
    ) -> None:
        self._registry = registry
        self._current_permissions = current_permissions
        self._approvals = approvals
        self._adapters: dict[str, _Adapter] = {}

    def bind(
        self,
        tool_id: str,
        *,
        invoke: ToolInvoker,
        resource: ResourceResolver,
    ) -> None:
        """Bind trusted functions to the EXACT current registry entry.

        Both callbacks are application-owned, not supplied by the model or an
        untrusted MCP server. No generic execution fallback is provided.
        """
        registration = self._registry.get(tool_id)
        self._adapters[tool_id] = _Adapter(registration, invoke, resource)

    def unbind(self, tool_id: str) -> None:
        self._adapters.pop(tool_id, None)

    def _adapter(self, tool_id: str) -> _Adapter:
        adapter = self._adapters.get(tool_id)
        if adapter is None:
            raise ToolAdapterMissing(f"No trusted adapter for: {tool_id}")
        # A tool removed and re-registered with the same ID is not equivalent.
        if self._registry.get(tool_id) is not adapter.registration:
            raise ToolExecutionDenied("Tool registration has changed")
        return adapter

    @staticmethod
    def _snapshot(arguments: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
        """Validate JSON compatibility and detach mutable caller arguments."""
        encoded = json.dumps(arguments, allow_nan=False, sort_keys=True)
        decoded = json.loads(encoded)
        if not isinstance(decoded, dict):
            raise ValueError("Tool arguments must form a JSON object")
        return cast("dict[str, JsonValue]", decoded)

    @staticmethod
    def _resolve(adapter: _Adapter, arguments: dict[str, JsonValue]) -> str | None:
        # Resolver gets its own copy so it cannot mutate the dispatched args.
        resolved = adapter.resource(ToolExecutor._snapshot(arguments))
        if resolved is not None and not resolved:
            raise ValueError("Resource resolver must return a nonempty ID or None")
        return resolved

    async def _decision(
        self, tool_id: str, resource_id: str | None
    ) -> PermissionResult:
        current = await self._current_permissions()
        result = current.evaluate(tool_id, resource_id=resource_id)
        # Reject a malformed provider rather than accepting a permission for
        # another resource or tool.
        if result.tool_id != tool_id or result.resource_id != resource_id:
            raise ToolExecutionDenied("Permission result does not match the call")
        return result

    async def execute(
        self, tool_id: str, *, arguments: Mapping[str, JsonValue]
    ) -> object:
        """Dispatch only after a current allow or a valid one-use approval.

        No raw ``resource_id`` argument is accepted: trusted code derives it
        from concrete call arguments. The native adapter handles SDK-level
        argument schema validation before performing any side effects.
        """
        adapter = self._adapter(tool_id)
        args = self._snapshot(arguments)
        resource_id = self._resolve(adapter, args)
        permission = await self._decision(tool_id, resource_id)
        if permission.decision is PermissionDecision.DENY:
            raise ToolExecutionDenied(permission.reason)

        if permission.decision is PermissionDecision.REQUIRE_APPROVAL:
            if self._approvals is None:
                raise ToolExecutionDenied("Human approval is unavailable")
            ticket = await self._approvals.request(permission, arguments=args)
            if ticket is None:
                raise ToolExecutionDenied("Human approval was refused")
            try:
                # The UI is asynchronous: registry, resolver and policy may
                # have changed while the user was deciding.
                if self._adapter(tool_id) is not adapter:
                    raise ToolExecutionDenied("Tool adapter changed during approval")
                if self._resolve(adapter, args) != resource_id:
                    raise ToolExecutionDenied("Resolved resource changed")
                fresh = await self._decision(tool_id, resource_id)
                if fresh.decision is not PermissionDecision.REQUIRE_APPROVAL:
                    # DENY blocks; ALLOW is a separate authorization and is
                    # intentionally not substituted for the approval flow.
                    raise ToolExecutionDenied("Permission changed during approval")
                if not self._approvals.consume(ticket, fresh, arguments=args):
                    raise ToolExecutionDenied("Approval token is invalid")
            finally:
                self._approvals.revoke(ticket)
        else:
            # Even allowed calls are checked against registry churn.
            if self._adapter(tool_id) is not adapter:
                raise ToolExecutionDenied("Tool adapter changed")
            if self._resolve(adapter, args) != resource_id:
                raise ToolExecutionDenied("Resolved resource changed")

        return await adapter.invoke(self._snapshot(args))

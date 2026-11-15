from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from guillotine.tools.contracts import ToolSecurity

if TYPE_CHECKING:
    from mcp.types import Tool as MCPTool
    from pydantic_ai.tools import Tool as PydanticTool


class ToolSource(StrEnum):
    LOCAL = "local"
    MCP = "mcp"


class DuplicateToolError(ValueError):
    """The same fully qualified tool is already registered."""


class UnknownToolError(LookupError):
    """The requested tool is not registered."""


@dataclass(frozen=True, slots=True)
class RegisteredTool:
    """Registry entry; definition is the original SDK-owned tool object.

    This wrapper is frozen, but the native definition may itself be mutable.
    No registered entry represents authorization to run the tool.
    """

    identifier: str
    source: ToolSource
    definition: PydanticTool[object] | MCPTool
    security: ToolSecurity
    server_id: str | None = None


class ToolRegistry:
    """Identify local and MCP tools without altering native tool definitions.

    Identifiers are namespaced: local:<name> or mcp:<server_id>:<name>.
    Colons are reserved delimiters, and component names must be nonblank.
    """

    def __init__(self) -> None:
        self._entries: dict[str, RegisteredTool] = {}

    @staticmethod
    def _component(value: str, *, field: str) -> str:
        if (
            not value
            or not value.strip()
            or value != value.strip()
            or ":" in value
            or any(ord(char) < 32 or ord(char) == 127 for char in value)
        ):
            raise ValueError(
                f"Invalid {field}: expected a nonblank value "
                "without colons or surrounding whitespace"
            )
        return value

    def register_local(
        self,
        definition: PydanticTool[object],
        *,
        security: ToolSecurity | None = None,
    ) -> RegisteredTool:
        """Register an explicitly named PydanticAI Tool, without executing it."""
        name = getattr(definition, "name", None)
        if not isinstance(name, str):
            raise ValueError("Local tool must have an explicit name")
        identifier = f"local:{self._component(name, field='tool name')}"
        entry = RegisteredTool(
            identifier=identifier,
            source=ToolSource.LOCAL,
            definition=definition,
            security=security if security is not None else ToolSecurity(),
        )
        return self._insert(entry)

    def register_mcp(
        self,
        definition: MCPTool,
        *,
        server_id: str,
        security: ToolSecurity | None = None,
    ) -> RegisteredTool:
        """Register an MCP SDK Tool with *trusted* Guillotine metadata.

        Never infer security from MCP annotations or server descriptions.
        """
        name = getattr(definition, "name", None)
        if not isinstance(name, str):
            raise ValueError("MCP tool must have a name")
        server = self._component(server_id, field="server id")
        identifier = f"mcp:{server}:{self._component(name, field='tool name')}"
        entry = RegisteredTool(
            identifier=identifier,
            source=ToolSource.MCP,
            server_id=server,
            definition=definition,
            security=security if security is not None else ToolSecurity(),
        )
        return self._insert(entry)

    def _insert(self, entry: RegisteredTool) -> RegisteredTool:
        if entry.identifier in self._entries:
            raise DuplicateToolError(f"Tool already registered: {entry.identifier}")
        self._entries[entry.identifier] = entry
        return entry

    def get(self, identifier: str) -> RegisteredTool:
        try:
            return self._entries[identifier]
        except KeyError as exc:
            raise UnknownToolError(f"Tool not found: {identifier}") from exc

    def list_tools(
        self, *, source: ToolSource | None = None
    ) -> tuple[RegisteredTool, ...]:
        """Return a snapshot of known entries, optionally filtered by origin."""
        return tuple(
            entry
            for entry in self._entries.values()
            if source is None or entry.source == source
        )

    def unregister(self, identifier: str) -> RegisteredTool:
        """Remove a registration, not any already-running tool invocation."""
        try:
            return self._entries.pop(identifier)
        except KeyError as exc:
            raise UnknownToolError(f"Tool not found: {identifier}") from exc

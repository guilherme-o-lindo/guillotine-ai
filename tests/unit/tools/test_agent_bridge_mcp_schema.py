"""MCP argument guidance and early rejection of invented tool fields."""

from __future__ import annotations

from typing import cast

import pytest
from mcp.types import Tool as MCPTool

from guillotine.core.approvals import JsonValue
from guillotine.tools.bridges.pydantic_ai import (
    execute_model_call,
    tool_catalog,
    validate_mcp_arguments,
)
from guillotine.tools.core.executor import ToolExecutor
from guillotine.tools.core.registry import RegisteredTool, ToolRegistry


def _registered_git_tool(name: str, schema: dict[str, object]) -> RegisteredTool:
    registry = ToolRegistry()
    native = MCPTool(name=name, input_schema=schema)
    return registry.register_mcp(native, server_id="git")


def test_git_catalog_exposes_names_and_required_fields_without_description() -> None:
    tool = _registered_git_tool(
        "git_log",
        {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "max_count": {"type": "integer", "minimum": 1, "default": 10},
            },
            "required": ["repo_path"],
        },
    )
    text = tool_catalog((tool,))
    assert "repo_path" in text
    assert "max_count" in text
    assert '"required":["repo_path"]' in text
    assert "git_log" in text


def test_git_log_accepts_correct_arguments() -> None:
    tool = _registered_git_tool(
        "git_log",
        {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "max_count": {"type": "integer", "minimum": 1},
            },
            "required": ["repo_path"],
        },
    )
    validate_mcp_arguments(tool, {"repo_path": "C:\\repo", "max_count": 5})


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"path": "C:\\repo"},
        {"repo_path": "C:\\repo", "n": 5},
        {"repo_path": "C:\\repo", "max_count": "five"},
        {"repo_path": "C:\\repo", "max_count": 0},
    ],
)
def test_git_log_rejects_missing_unknown_or_invalid_arguments(
    arguments: dict[str, JsonValue],
) -> None:
    tool = _registered_git_tool(
        "git_log",
        {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "max_count": {"type": "integer", "minimum": 1},
            },
            "required": ["repo_path"],
        },
    )
    with pytest.raises(ValueError):
        validate_mcp_arguments(tool, arguments)


def test_git_branch_requires_branch_type() -> None:
    tool = _registered_git_tool(
        "git_branch",
        {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "branch_type": {"type": "string"},
            },
            "required": ["repo_path", "branch_type"],
        },
    )
    with pytest.raises(ValueError):
        validate_mcp_arguments(tool, {"repo_path": "C:\\repo"})
    validate_mcp_arguments(tool, {"repo_path": "C:\\repo", "branch_type": "all"})


def test_mcp_schema_does_not_follow_refs() -> None:
    tool = _registered_git_tool(
        "git_status",
        {
            "type": "object",
            "properties": {"repo_path": {"$ref": "https://example.com/schema"}},
            "required": ["repo_path"],
        },
    )
    with pytest.raises(ValueError):
        validate_mcp_arguments(tool, {"repo_path": "C:\\repo"})


@pytest.mark.asyncio
async def test_invalid_mcp_arguments_never_reach_executor() -> None:
    tool = _registered_git_tool(
        "git_status",
        {
            "type": "object",
            "properties": {"repo_path": {"type": "string"}},
            "required": ["repo_path"],
        },
    )
    registry = ToolRegistry()
    assert isinstance(tool.definition, MCPTool)
    registry.register_mcp(tool.definition, server_id="git")
    registered = registry.get("mcp:git:git_status")

    class ForbiddenExecutor:
        async def execute(self, *_args: object, **_kwargs: object) -> object:
            raise AssertionError("Executor must not be called for invalid MCP input")

    result = await execute_model_call(
        "mcp:git:git_status",
        '{"path":"C:\\\\repo"}',
        allowed={registered.identifier: registered},
        registry=registry,
        executor=cast("ToolExecutor", ForbiddenExecutor()),
    )
    assert "Argumentos inválidos" in result

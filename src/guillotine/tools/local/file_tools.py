"""Opt-in read-only local file tools bound to the existing executor.

The configured root is trusted application configuration, never model input.
These guards are not an operating-system sandbox against filesystem races.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai.tools import Tool

from guillotine.core.approvals import JsonValue
from guillotine.tools.core.contracts import ToolEffect, ToolSecurity
from guillotine.tools.core.executor import ToolExecutor
from guillotine.tools.core.registry import ToolRegistry
from guillotine.tools.local.file_reader import LocalFileReader

LIST_ID = "local:list_directory"
READ_ID = "local:read_file"
SEARCH_ID = "local:search_files"


class _Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    path: str = Field(default=".", min_length=1, max_length=4096)


class _SearchArguments(_Arguments):
    query: str = Field(min_length=1, max_length=200)


class _ReadArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    path: str = Field(min_length=1, max_length=4096)


def register_file_tools(
    registry: ToolRegistry, executor: ToolExecutor, *, root: Path
) -> tuple[str, str, str]:
    """Register three READ-only tools for one explicitly authorized directory.

    Permissions and approval remain owned by ToolExecutor. The resource ID
    identifies the exact canonical path, not an agent-supplied resource token.
    """
    reader = LocalFileReader(root)
    security = ToolSecurity(effects=frozenset({ToolEffect.READ}))

    async def list_directory(path: str = ".") -> dict[str, object]:
        """List entries below the authorized file root, using a relative path."""
        return await asyncio.to_thread(reader.list_directory, path)

    async def read_file(path: str) -> dict[str, object]:
        """Read a bounded UTF-8 file by its path relative to the authorized root."""
        return await asyncio.to_thread(reader.read_file, path)

    async def search_files(query: str, path: str = ".") -> dict[str, object]:
        """Find text in bounded files below a relative directory path."""
        return await asyncio.to_thread(reader.search_files, query, path)

    def list_resource(arguments: Mapping[str, JsonValue]) -> str:
        args = _Arguments.model_validate(arguments)
        target = reader.resolve_path(args.path)
        if not target.is_dir():
            raise ValueError("Path is not a directory")
        return target.as_uri()

    def read_resource(arguments: Mapping[str, JsonValue]) -> str:
        args = _ReadArguments.model_validate(arguments)
        target = reader.resolve_path(args.path)
        if not target.is_file():
            raise ValueError("Path is not a regular file")
        return target.as_uri()

    def search_resource(arguments: Mapping[str, JsonValue]) -> str:
        args = _SearchArguments.model_validate(arguments)
        target = reader.resolve_path(args.path)
        if not target.is_dir():
            raise ValueError("Search path is not a directory")
        return target.as_uri()

    async def invoke_list(arguments: dict[str, JsonValue]) -> object:
        args = _Arguments.model_validate(arguments)
        return await list_directory(args.path)

    async def invoke_read(arguments: dict[str, JsonValue]) -> object:
        args = _ReadArguments.model_validate(arguments)
        return await read_file(args.path)

    async def invoke_search(arguments: dict[str, JsonValue]) -> object:
        args = _SearchArguments.model_validate(arguments)
        return await search_files(args.query, args.path)

    list_entry = registry.register_local(
        Tool(list_directory, name="list_directory"), security=security
    )
    read_entry = registry.register_local(
        Tool(read_file, name="read_file"), security=security
    )
    search_entry = registry.register_local(
        Tool(search_files, name="search_files"), security=security
    )
    executor.bind(list_entry.identifier, invoke=invoke_list, resource=list_resource)
    executor.bind(read_entry.identifier, invoke=invoke_read, resource=read_resource)
    executor.bind(
        search_entry.identifier, invoke=invoke_search, resource=search_resource
    )
    return (list_entry.identifier, read_entry.identifier, search_entry.identifier)

"""Explicit user-owned MCP configuration; never accept server setup from an LLM.

The configuration selects tools and supplies application-owned resource resolvers.
It does NOT grant tool permissions: those remain in PermissionStore/ToolExecutor.
"""

from __future__ import annotations

import hashlib
import ipaddress
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from mcp import StdioServerParameters
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from guillotine.core.approvals import JsonValue
from guillotine.tools.core.contracts import ToolEffect, ToolSecurity
from guillotine.tools.core.executor import ResourceResolver
from guillotine.tools.mcp.client import (
    MCPClient,
    http_session_factory,
    stdio_session_factory,
)
from guillotine.tools.mcp.manager import MCPManager


class _ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class NoResource(_ConfigModel):
    """For tools whose entire operation has no distinct resource scope."""

    kind: Literal["none"]


class QueryResource(_ConfigModel):
    """Bind each read-only search invocation to the exact query without logging it."""

    kind: Literal["query"]
    argument: str = Field(min_length=1)

    @field_validator("argument")
    @classmethod
    def valid_argument(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("Query argument must be a nonblank JSON field name")
        return value


class ReferenceTokenResource(_ConfigModel):
    """Scope a result-reference lookup to one opaque DuckDuckGo ref token."""

    kind: Literal["reference_token"]
    argument: str = Field(min_length=1)

    @field_validator("argument")
    @classmethod
    def valid_argument(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("Reference argument must be a nonblank JSON field name")
        return value


class URLResource(_ConfigModel):
    """Bind an outbound HTTP URL argument to a validated, opaque resource ID.

    This is an input guard, NOT an SSRF-safe transport. The MCP server may
    independently resolve DNS, follow redirects, or accept ref:// tokens.
    """

    kind: Literal["url"]
    argument: str = Field(min_length=1)

    @field_validator("argument")
    @classmethod
    def valid_argument(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("URL argument must be a nonblank JSON field name")
        return value


class RepositoryResource(_ConfigModel):
    """Bind a Git tool invocation to precisely one configured repository."""

    kind: Literal["repository"]
    argument: str = Field(min_length=1)
    root: Path

    @field_validator("argument")
    @classmethod
    def valid_argument(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("Repository argument must be a nonblank JSON field name")
        return value

    @field_validator("root")
    @classmethod
    def valid_root(cls, root: Path) -> Path:
        if not root.is_absolute():
            raise ValueError("Repository root must be an absolute path")
        canonical = root.resolve()
        if not canonical.is_dir() or not (canonical / ".git").exists():
            raise ValueError("Repository root must be an existing Git repository")
        return canonical


class FileResource(_ConfigModel):
    """Canonicalize and confine one file argument beneath a trusted directory."""

    kind: Literal["file"]
    argument: str = Field(min_length=1)
    root: Path

    @field_validator("argument")
    @classmethod
    def valid_argument(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("File argument must be a nonblank JSON field name")
        return value

    @field_validator("root")
    @classmethod
    def absolute_root(cls, root: Path) -> Path:
        if not root.is_absolute():
            raise ValueError("File scope root must be an absolute path")
        return root.resolve()


type ResourceSpec = Annotated[
    NoResource
    | FileResource
    | QueryResource
    | ReferenceTokenResource
    | URLResource
    | RepositoryResource,
    Field(discriminator="kind"),
]


class SelectedTool(_ConfigModel):
    name: str = Field(min_length=1)
    effects: tuple[ToolEffect, ...] = Field(min_length=1)
    resource: ResourceSpec

    @field_validator("name")
    @classmethod
    def valid_name(cls, name: str) -> str:
        if (
            name != name.strip()
            or ":" in name
            or any(ord(char) < 32 or ord(char) == 127 for char in name)
        ):
            raise ValueError("Invalid tool name")
        return name

    @model_validator(mode="after")
    def enforce_scope_effects(self) -> SelectedTool:
        if isinstance(
            self.resource, (QueryResource, ReferenceTokenResource, URLResource)
        ) and any(
            effect not in {ToolEffect.READ, ToolEffect.NETWORK}
            for effect in self.effects
        ):
            raise ValueError(
                "Query/reference/URL scopes only support read/network effects"
            )
        if isinstance(self.resource, RepositoryResource) and set(self.effects) != {
            ToolEffect.READ
        }:
            raise ValueError("Repository scope is read-only in this version")
        return self

    @field_validator("effects")
    @classmethod
    def known_effects(cls, effects: tuple[ToolEffect, ...]) -> tuple[ToolEffect, ...]:
        if ToolEffect.UNKNOWN in effects:
            raise ValueError("Tools must explicitly declare known security effects")
        if len(set(effects)) != len(effects):
            raise ValueError("Duplicate security effects")
        return effects


class ServerSpec(_ConfigModel):
    id: str = Field(min_length=1)
    transport: Literal["stdio", "streamable-http"]
    command: str | None = None
    args: tuple[str, ...] = ()
    url: str | None = None
    tools: tuple[SelectedTool, ...] = ()

    @model_validator(mode="after")
    def valid_transport(self) -> ServerSpec:
        if (
            self.id != self.id.strip()
            or ":" in self.id
            or any(ord(char) < 32 or ord(char) == 127 for char in self.id)
        ):
            raise ValueError("Invalid MCP server ID")
        if len({tool.name for tool in self.tools}) != len(self.tools):
            raise ValueError("Duplicate selected tool names")
        if self.transport == "stdio":
            if not self.command or not self.command.strip() or self.url is not None:
                raise ValueError("stdio requires command and forbids url")
        elif self.command is not None or self.args or not self.url:
            raise ValueError("HTTP requires url and forbids command/args")
        if (
            self.transport == "streamable-http"
            and self.url is not None
            and not self.url.startswith("https://")
            and not self.url.startswith(
                ("http://localhost:", "http://127.0.0.1:", "http://[::1]:")
            )
        ):
            raise ValueError("HTTP MCP requires HTTPS except for loopback")
        return self


class MCPConfiguration(_ConfigModel):
    version: Literal[1] = 1
    servers: tuple[ServerSpec, ...] = ()

    @model_validator(mode="after")
    def unique_servers(self) -> MCPConfiguration:
        if len({server.id for server in self.servers}) != len(self.servers):
            raise ValueError("Duplicate MCP server IDs")
        return self


def config_path() -> Path:
    """Use user-specific configuration, not files in a potentially untrusted repo."""
    override = os.environ.get("GUILLOTINE_MCP_CONFIG")
    if override:
        return Path(override).expanduser().resolve()
    base = os.environ.get("APPDATA") if os.name == "nt" else None
    home = Path(base) if base else Path.home() / ".config"
    return home / "guillotine" / "mcp.json"


def read_config(path: Path) -> MCPConfiguration:
    """Fail closed on an invalid file. Missing config is handled by the caller."""
    return MCPConfiguration.model_validate_json(path.read_text(encoding="utf-8"))


def write_config(path: Path, config: MCPConfiguration) -> None:
    """Persist trusted user commands atomically; never write credentials here."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            stream.write(config.model_dump_json(indent=2))
            stream.write("\n")
        if os.name != "nt":
            temporary.chmod(0o600)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


_HOST_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")
_NONPUBLIC_SUFFIXES = (
    ".localhost",
    ".localdomain",
    ".local",
    ".internal",
    ".home.arpa",
    ".test",
    ".invalid",
    ".example",
    ".onion",
)


def _validated_public_url(raw: str) -> str:
    """Apply conservative URL input checks before permission evaluation.

    No DNS lookup is performed here. Enforce SSRF protection at the actual
    network boundary as well; a domain may resolve to a private address or
    redirect to one after this function returns.
    """
    if (
        not raw
        or len(raw) > 4096
        or raw != raw.strip()
        or any(ord(char) < 33 or ord(char) > 126 for char in raw)
        or "\\" in raw
    ):
        raise ValueError("Invalid outbound URL")
    # The MCP server accepts ref://, but an opaque token cannot be verified
    # here. Fail closed until server-side dereferencing is controlled.
    if raw.startswith("ref://"):
        raise PermissionError("ref:// fetching requires server-side destination checks")
    try:
        parsed = urlsplit(raw)
        hostname = parsed.hostname
        port = parsed.port  # raises ValueError for malformed ports
    except ValueError as exc:
        raise ValueError("Malformed outbound URL") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or "@" in parsed.netloc
        or "%" in parsed.netloc
        or "#" in raw
    ):
        raise ValueError(
            "Only public HTTP(S) URLs without credentials or fragments are supported"
        )
    if port is not None and port != (443 if parsed.scheme == "https" else 80):
        raise PermissionError("Nondefault URL ports are not allowed")
    host = hostname.lower()
    # Restrict to conventional fully-qualified ASCII DNS names. This denies
    # IP literals, short names, numeric host obfuscations and IPv6 literals.
    if (
        "." not in host
        or host.endswith(".")
        or len(host) > 253
        or host == "localhost"
        or host.endswith(_NONPUBLIC_SUFFIXES)
        or not all(_HOST_LABEL.fullmatch(label) for label in host.split("."))
        or host.split(".")[-1].isdigit()
    ):
        raise PermissionError("URL host is not an allowed public DNS name")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise PermissionError("IP literal destinations are not allowed")
    return raw


def resource_resolver(spec: ResourceSpec) -> ResourceResolver:
    """Factory for a trusted resolver; no path/resource ID is supplied by the LLM."""
    if isinstance(spec, NoResource):

        def none_resource(_arguments: Mapping[str, JsonValue]) -> None:
            return None

        return none_resource

    if isinstance(spec, QueryResource):
        argument = spec.argument

        def query_resource(arguments: Mapping[str, JsonValue]) -> str:
            raw = arguments.get(argument)
            if not isinstance(raw, str) or not raw.strip():
                raise ValueError(f"Expected a nonempty search query: {argument}")
            if len(raw) > 4096:
                raise ValueError("Search query exceeds the maximum permitted length")
            # An opaque ID: search text does not enter the permission/audit database.
            digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            return f"query:sha256:{digest}"

        return query_resource

    if isinstance(spec, ReferenceTokenResource):
        argument = spec.argument

        def reference_resource(arguments: Mapping[str, JsonValue]) -> str:
            raw = arguments.get(argument)
            if not isinstance(raw, str):
                raise ValueError(f"Expected a DuckDuckGo reference token: {argument}")
            # Tokens may be written with the ref:// prefix or as bare IDs.
            # Never accept arbitrary URLs or control characters as a reference.
            token_id = raw.removeprefix("ref://")
            if re.fullmatch(r"[A-Za-z0-9_-]{1,128}", token_id) is None:
                raise ValueError("Invalid DuckDuckGo reference token")
            digest = hashlib.sha256(token_id.encode("ascii")).hexdigest()
            # Keep raw token values out of audit entries and policy resource IDs.
            return f"reference:sha256:{digest}"

        return reference_resource

    if isinstance(spec, URLResource):
        argument = spec.argument

        def url_resource(arguments: Mapping[str, JsonValue]) -> str:
            raw = arguments.get(argument)
            if not isinstance(raw, str):
                raise ValueError(f"Expected an HTTP(S) URL: {argument}")
            validated = _validated_public_url(raw)
            digest = hashlib.sha256(validated.encode("ascii")).hexdigest()
            return f"url:sha256:{digest}"

        return url_resource

    if isinstance(spec, RepositoryResource):
        root = spec.root.resolve()
        argument = spec.argument

        def repository_resource(arguments: Mapping[str, JsonValue]) -> str:
            raw = arguments.get(argument)
            if not isinstance(raw, str) or not raw.strip():
                raise ValueError(f"Expected an absolute repository path: {argument}")
            supplied = Path(raw)
            if not supplied.is_absolute():
                raise PermissionError("Repository path must be absolute")
            if supplied.resolve() != root:
                raise PermissionError("Tool call targets a different repository")
            return root.as_uri()

        return repository_resource

    root = spec.root.resolve()
    argument = spec.argument

    def file_resource(arguments: Mapping[str, JsonValue]) -> str:
        raw = arguments.get(argument)
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(f"Expected a nonempty file path argument: {argument}")
        supplied = Path(raw)
        if not supplied.is_absolute():
            raise PermissionError("File tool arguments must use absolute paths")
        candidate = supplied.resolve()
        if not candidate.is_relative_to(root) or candidate == root:
            raise PermissionError("File is outside the configured resource scope")
        return candidate.as_uri()

    return file_resource


def client_for_server(server: ServerSpec) -> MCPClient:
    """Use the exact same trusted transport configuration for inspect and connect."""
    if server.transport == "stdio":
        assert server.command is not None
        return MCPClient(
            stdio_session_factory(
                StdioServerParameters(command=server.command, args=list(server.args))
            )
        )
    assert server.url is not None
    return MCPClient(http_session_factory(server.url))


async def connect_configured_servers(
    manager: MCPManager, configuration: MCPConfiguration
) -> None:
    """Bind explicitly selected MCP tools with application-owned resolvers."""
    for server in configuration.servers:
        if not server.tools:
            continue  # configured but not selected: never start this server
        await manager.connect(
            server.id,
            client_for_server(server),
            resolvers={
                tool.name: resource_resolver(tool.resource) for tool in server.tools
            },
            security={
                tool.name: ToolSecurity(effects=frozenset(tool.effects))
                for tool in server.tools
            },
        )

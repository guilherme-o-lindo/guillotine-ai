"""URL scopes are conservative argument guards, not an SSRF-safe transport."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from guillotine.core.approvals import JsonValue
from guillotine.core.mcp_configuration import (
    MCPConfiguration,
    SelectedTool,
    ServerSpec,
    URLResource,
    resource_resolver,
)
from guillotine.tools.core.contracts import ToolEffect
from guillotine.tools.core.executor import ResourceResolver


def _resolver() -> ResourceResolver:
    return resource_resolver(URLResource(kind="url", argument="url"))


def test_url_resource_returns_opaque_stable_identifier() -> None:
    resolver = _resolver()
    url = "https://www.python.org/dev/peps/?q=asyncio"
    result = resolver({"url": url})
    assert result is not None
    assert result.startswith("url:sha256:")
    assert url not in result
    assert result == resolver({"url": url})
    assert result != resolver({"url": "https://www.python.org/"})


@pytest.mark.parametrize(
    "url",
    [
        "",
        "ref://abc123",
        "abc123",
        "file:///etc/passwd",
        "ftp://www.example.org/path",
        "http://localhost/x",
        "http://localhost.localdomain/x",
        "http://service.internal/path",
        "http://router.local/",
        "http://metadata.google.internal/",
        "http://127.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "http://2130706433/",
        "http://0x7f000001/",
        "http://user:password@www.example.org/",
        "https://www.example.org:8443/",
        "http://www.example.org:8080/",
        "https://www.example.org/#section",
        "https://www.example.org\\@localhost/",
        " https://www.example.org/",
        "https://www.example.org/\n",
        "https://www.example.org/%09" + "x" * 4096,
        "https://www.example.org./",
        "https://www.example.org%2flocalhost/",
        "https://www.example.org:abc/",
    ],
)
def test_url_resource_rejects_suspicious_inputs(url: str) -> None:
    resolver = _resolver()
    with pytest.raises((PermissionError, ValueError)):
        resolver({"url": url})


@pytest.mark.parametrize("arguments", [{}, {"url": 123}, {"url": None}])
def test_url_resource_rejects_missing_or_nonstring_value(
    arguments: dict[str, JsonValue],
) -> None:
    with pytest.raises(ValueError):
        _resolver()(arguments)


def test_url_scope_only_permits_read_or_network_effects() -> None:
    resource = URLResource(kind="url", argument="url")
    SelectedTool(name="fetch_content", effects=(ToolEffect.NETWORK,), resource=resource)
    with pytest.raises(ValidationError):
        SelectedTool(
            name="fetch_content", effects=(ToolEffect.WRITE,), resource=resource
        )


def test_url_scope_survives_configuration_roundtrip() -> None:
    config = MCPConfiguration(
        servers=(
            ServerSpec(
                id="duckduckgo",
                transport="stdio",
                command="uvx",
                tools=(
                    SelectedTool(
                        name="fetch_content",
                        effects=(ToolEffect.NETWORK,),
                        resource=URLResource(kind="url", argument="url"),
                    ),
                ),
            ),
        ),
    )
    assert MCPConfiguration.model_validate_json(config.model_dump_json()) == config

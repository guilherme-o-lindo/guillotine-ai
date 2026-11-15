"""Reference token resources are strict and do not leak tokens into audit IDs."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from guillotine.core.mcp_configuration import (
    MCPConfiguration,
    ReferenceTokenResource,
    SelectedTool,
    ServerSpec,
    resource_resolver,
)
from guillotine.tools.core.contracts import ToolEffect


def test_reference_token_accepts_prefixed_and_bare_id() -> None:
    resolver = resource_resolver(
        ReferenceTokenResource(kind="reference_token", argument="token")
    )
    full = resolver({"token": "ref://abc_123-X"})
    assert full is not None and full.startswith("reference:sha256:")
    assert full == resolver({"token": "abc_123-X"})
    assert "abc_123-X" not in full
    assert full != resolver({"token": "def_456"})


@pytest.mark.parametrize(
    "token",
    [
        "",
        "ref://",
        "ref://../private",
        "https://example.org/",
        "http://localhost",
        "ref://a/b",
        "ref://a?b",
        "ref://a\n",
        "ref://a b",
        "ref://" + "x" * 129,
    ],
)
def test_reference_token_rejects_invalid_values(token: str) -> None:
    resolver = resource_resolver(
        ReferenceTokenResource(kind="reference_token", argument="token")
    )
    with pytest.raises(ValueError):
        resolver({"token": token})


def test_reference_token_missing_or_non_string_rejected() -> None:
    resolver = resource_resolver(
        ReferenceTokenResource(kind="reference_token", argument="token")
    )
    for args in ({}, {"token": 123}, {"token": None}):
        with pytest.raises(ValueError):
            resolver(args)


def test_reference_scope_only_allows_read_or_network_effect() -> None:
    resource = ReferenceTokenResource(kind="reference_token", argument="token")
    SelectedTool(name="expand_link", effects=(ToolEffect.READ,), resource=resource)
    with pytest.raises(ValidationError):
        SelectedTool(name="expand_link", effects=(ToolEffect.WRITE,), resource=resource)


def test_reference_scope_survives_native_configuration_roundtrip() -> None:
    config = MCPConfiguration(
        servers=(
            ServerSpec(
                id="duckduckgo",
                transport="stdio",
                command="uvx",
                tools=(
                    SelectedTool(
                        name="expand_link",
                        effects=(ToolEffect.READ,),
                        resource=ReferenceTokenResource(
                            kind="reference_token", argument="token"
                        ),
                    ),
                ),
            ),
        ),
    )
    assert MCPConfiguration.model_validate_json(config.model_dump_json()) == config

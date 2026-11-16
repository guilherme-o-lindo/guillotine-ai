"""The local fetch tool must never bypass the current permission boundary."""

from __future__ import annotations

import pytest

from guillotine.core.mcp_configuration import URLResource, resource_resolver
from guillotine.core.permissions import (
    PermissionDecision,
    PermissionManager,
    PermissionProfile,
    PermissionRule,
)
from guillotine.tools.core.executor import ToolExecutionDenied, ToolExecutor
from guillotine.tools.core.registry import ToolRegistry
from guillotine.tools.local import web_fetch as local_safe_fetch
from guillotine.tools.local.html_extract import ExtractedPage, PageLink
from guillotine.tools.local.safe_fetch import FetchResult


@pytest.mark.asyncio
async def test_fetch_denied_without_ever_touching_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = ToolRegistry()

    async def current() -> PermissionManager:
        return PermissionManager(registry, profile=PermissionProfile.CUSTOM, rules=())

    executor = ToolExecutor(registry, current)
    local_safe_fetch.register_safe_fetch(registry, executor)

    def forbidden_network(*_args: object, **_kwargs: object) -> FetchResult:
        pytest.fail("network must not be accessed on a denied call")

    monkeypatch.setattr(local_safe_fetch, "fetch_public_page", forbidden_network)
    with pytest.raises(ToolExecutionDenied):
        await executor.execute(
            local_safe_fetch.TOOL_ID, arguments={"url": "https://example.org/"}
        )


@pytest.mark.asyncio
async def test_allowed_fetch_uses_guarded_reader_and_returns_final_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = ToolRegistry()
    url = "https://example.org/article"
    resource = resource_resolver(URLResource(kind="url", argument="url"))({"url": url})
    assert resource is not None

    async def current() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(
                PermissionRule(
                    local_safe_fetch.TOOL_ID, resource, PermissionDecision.ALLOW
                ),
            ),
        )

    executor = ToolExecutor(registry, current)
    local_safe_fetch.register_safe_fetch(registry, executor)
    called: list[str] = []

    def fake_fetch(page_url: str, **_kwargs: object) -> FetchResult:
        called.append(page_url)
        return FetchResult(
            url="https://example.org/final",
            status=200,
            content_type="text/html",
            text="texto",
        )

    monkeypatch.setattr(local_safe_fetch, "fetch_public_page", fake_fetch)
    result = await executor.execute(local_safe_fetch.TOOL_ID, arguments={"url": url})
    assert called == [url]
    assert "https://example.org/final" in str(result)
    assert "texto" in str(result)


@pytest.mark.asyncio
async def test_rejects_invalid_url_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = ToolRegistry()

    async def current() -> PermissionManager:
        return PermissionManager(registry, profile=PermissionProfile.CUSTOM, rules=())

    executor = ToolExecutor(registry, current)
    local_safe_fetch.register_safe_fetch(registry, executor)

    def forbidden_network(*_args: object, **_kwargs: object) -> FetchResult:
        pytest.fail("invalid URLs must not reach network")

    monkeypatch.setattr(local_safe_fetch, "fetch_public_page", forbidden_network)
    with pytest.raises((ValueError, PermissionError)):
        await executor.execute(
            local_safe_fetch.TOOL_ID, arguments={"url": "http://localhost/"}
        )
    with pytest.raises((ValueError, PermissionError)):
        await executor.execute(
            local_safe_fetch.TOOL_ID, arguments={"url": "ref://opaque"}
        )


@pytest.mark.asyncio
async def test_allowed_fetch_returns_structured_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = ToolRegistry()
    url = "https://example.org/article"
    resource = resource_resolver(URLResource(kind="url", argument="url"))({"url": url})
    assert resource is not None

    async def current() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(
                PermissionRule(
                    local_safe_fetch.TOOL_ID, resource, PermissionDecision.ALLOW
                ),
            ),
        )

    executor = ToolExecutor(registry, current)
    local_safe_fetch.register_safe_fetch(registry, executor)

    def fake_fetch(page_url: str, **_kwargs: object) -> FetchResult:
        assert page_url == url
        page = ExtractedPage(
            url=url,
            title="Título",
            description="Resumo",
            content="Conteúdo principal",
            links=(PageLink(text="Documentação", url="https://example.org/docs"),),
        )
        return FetchResult(
            url=url,
            status=200,
            content_type="text/html",
            text=page.content,
            page=page,
        )

    monkeypatch.setattr(local_safe_fetch, "fetch_public_page", fake_fetch)
    response = await executor.execute(local_safe_fetch.TOOL_ID, arguments={"url": url})
    assert '"title": "Título"' in str(response)
    assert '"description": "Resumo"' in str(response)
    assert '"text": "Documentação"' in str(response)
    assert "Conteúdo principal" in str(response)

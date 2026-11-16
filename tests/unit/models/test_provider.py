from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from guillotine.core.config import settings
from guillotine.models import provider as provider_module


@pytest.mark.asyncio
async def test_model_lifecycle_creates_provider_and_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider_constructor = Mock()
    model_constructor = Mock()

    mock_client = Mock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    client_constructor = Mock(return_value=mock_client)

    monkeypatch.setattr(
        provider_module.httpx2,
        "AsyncClient",
        client_constructor,
    )
    monkeypatch.setattr(
        provider_module,
        "OpenAIProvider",
        provider_constructor,
    )
    monkeypatch.setattr(
        provider_module,
        "OpenAIChatModel",
        model_constructor,
    )

    expected_provider = Mock()
    expected_model = Mock()

    provider_constructor.return_value = expected_provider
    model_constructor.return_value = expected_model

    async with provider_module.model_lifecycle() as model:
        assert model is expected_model

    client_constructor.assert_called_once()
    provider_constructor.assert_called_once_with(
        base_url=settings.BASE_URL,
        api_key=settings.API_KEY,
        http_client=mock_client,
    )
    model_constructor.assert_called_once_with(
        settings.MODEL,
        provider=expected_provider,
    )

    mock_client.__aenter__.assert_awaited_once()
    mock_client.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_model_lifecycle_closes_client_when_initialization_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_client = Mock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr(
        provider_module.httpx2,
        "AsyncClient",
        Mock(return_value=mock_client),
    )
    monkeypatch.setattr(
        provider_module,
        "OpenAIProvider",
        Mock(side_effect=RuntimeError("Falha de inicialização")),
    )

    with pytest.raises(RuntimeError, match="Falha de inicialização"):
        async with provider_module.model_lifecycle():
            pass

    mock_client.__aenter__.assert_awaited_once()
    mock_client.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_model_lifecycle_creates_independent_clients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clients: list[Mock] = []

    def create_client(*args: Any, **kwargs: Any) -> Mock:
        client = Mock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        clients.append(client)
        return client

    monkeypatch.setattr(
        provider_module.httpx2,
        "AsyncClient",
        create_client,
    )
    monkeypatch.setattr(
        provider_module,
        "OpenAIProvider",
        Mock(),
    )
    monkeypatch.setattr(
        provider_module,
        "OpenAIChatModel",
        Mock(),
    )

    async with provider_module.model_lifecycle():
        pass

    async with provider_module.model_lifecycle():
        pass

    assert len(clients) == 2
    assert clients[0] is not clients[1]

    for client in clients:
        client.__aenter__.assert_awaited_once()
        client.__aexit__.assert_awaited_once()

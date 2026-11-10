from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from guillotine.core import lifecycle


def make_async_context(value: object) -> MagicMock:
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=value)
    context.__aexit__ = AsyncMock(return_value=None)
    return context


@pytest.mark.asyncio
async def test_lifespan_initializes_and_provides_conversation_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = Mock()
    checkpointer = Mock()
    agent = Mock()
    workflow = Mock()
    service = Mock()

    memory = Mock()
    memory.initialize = AsyncMock()

    model_context = make_async_context(model)
    checkpointer_context = make_async_context(checkpointer)

    create_agent_mock = Mock(return_value=agent)
    build_workflow_mock = Mock(return_value=workflow)
    conversation_service_mock = Mock(return_value=service)

    monkeypatch.setattr(
        lifecycle,
        "model_lifecycle",
        Mock(return_value=model_context),
    )
    monkeypatch.setattr(
        lifecycle,
        "get_checkpointer",
        Mock(return_value=checkpointer_context),
    )
    monkeypatch.setattr(
        lifecycle,
        "MemoryManager",
        Mock(return_value=memory),
    )
    monkeypatch.setattr(
        lifecycle,
        "create_agent",
        create_agent_mock,
    )
    monkeypatch.setattr(
        lifecycle,
        "build_workflow",
        build_workflow_mock,
    )
    monkeypatch.setattr(
        lifecycle,
        "ConversationService",
        conversation_service_mock,
    )

    async with lifecycle.lifespan() as result:
        assert result is service

        memory.initialize.assert_awaited_once()
        create_agent_mock.assert_called_once_with(model)

        build_workflow_mock.assert_called_once_with(
            memory,
            checkpointer,
            agent,
        )

        conversation_service_mock.assert_called_once_with(
            memory,
            workflow,
            checkpointer,
        )

    model_context.__aenter__.assert_awaited_once()
    model_context.__aexit__.assert_awaited_once()

    checkpointer_context.__aenter__.assert_awaited_once()
    checkpointer_context.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_closes_resources_after_context_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model_context = make_async_context(Mock())
    checkpointer_context = make_async_context(Mock())

    memory = Mock()
    memory.initialize = AsyncMock()

    monkeypatch.setattr(
        lifecycle,
        "model_lifecycle",
        Mock(return_value=model_context),
    )
    monkeypatch.setattr(
        lifecycle,
        "get_checkpointer",
        Mock(return_value=checkpointer_context),
    )
    monkeypatch.setattr(
        lifecycle,
        "MemoryManager",
        Mock(return_value=memory),
    )
    monkeypatch.setattr(lifecycle, "create_agent", Mock())
    monkeypatch.setattr(lifecycle, "build_workflow", Mock())
    monkeypatch.setattr(
        lifecycle,
        "ConversationService",
        Mock(),
    )

    async with lifecycle.lifespan():
        model_context.__aexit__.assert_not_awaited()
        checkpointer_context.__aexit__.assert_not_awaited()

    checkpointer_context.__aexit__.assert_awaited_once()
    model_context.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_closes_model_client_when_memory_initialization_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model_context = make_async_context(Mock())

    memory = Mock()
    memory.initialize = AsyncMock(
        side_effect=RuntimeError("Falha ao inicializar memória"),
    )

    checkpointer_factory = Mock()

    monkeypatch.setattr(
        lifecycle,
        "model_lifecycle",
        Mock(return_value=model_context),
    )
    monkeypatch.setattr(
        lifecycle,
        "MemoryManager",
        Mock(return_value=memory),
    )
    monkeypatch.setattr(
        lifecycle,
        "get_checkpointer",
        checkpointer_factory,
    )

    with pytest.raises(
        RuntimeError,
        match="Falha ao inicializar memória",
    ):
        async with lifecycle.lifespan():
            pass

    model_context.__aexit__.assert_awaited_once()
    checkpointer_factory.assert_not_called()


@pytest.mark.asyncio
async def test_lifespan_closes_model_client_when_checkpointer_initialization_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model_context = make_async_context(Mock())

    checkpointer_context = make_async_context(Mock())
    checkpointer_context.__aenter__ = AsyncMock(
        side_effect=RuntimeError("Falha ao inicializar checkpointer"),
    )

    memory = Mock()
    memory.initialize = AsyncMock()

    monkeypatch.setattr(
        lifecycle,
        "model_lifecycle",
        Mock(return_value=model_context),
    )
    monkeypatch.setattr(
        lifecycle,
        "get_checkpointer",
        Mock(return_value=checkpointer_context),
    )
    monkeypatch.setattr(
        lifecycle,
        "MemoryManager",
        Mock(return_value=memory),
    )
    monkeypatch.setattr(
        lifecycle,
        "create_agent",
        Mock(),
    )

    with pytest.raises(
        RuntimeError,
        match="Falha ao inicializar checkpointer",
    ):
        async with lifecycle.lifespan():
            pass

    memory.initialize.assert_awaited_once()
    checkpointer_context.__aenter__.assert_awaited_once()
    checkpointer_context.__aexit__.assert_not_awaited()
    model_context.__aexit__.assert_awaited_once()

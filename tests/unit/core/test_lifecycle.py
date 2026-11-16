from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from guillotine.core import lifecycle
from guillotine.tools.core.executor import ToolExecutor
from guillotine.tools.core.registry import ToolRegistry


def make_async_context(value: object) -> MagicMock:
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=value)
    context.__aexit__ = AsyncMock(return_value=None)
    return context


@pytest.mark.asyncio
async def test_lifespan_initializes_and_provides_conversation_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GUILLOTINE_FILE_ROOT", raising=False)
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
        create_agent_mock.assert_called_once()

        args, kwargs = create_agent_mock.call_args

        assert args == (model,)
        assert isinstance(kwargs["registry"], ToolRegistry)
        assert isinstance(kwargs["executor"], ToolExecutor)
        registered_tools = kwargs["registry"].list_tools()

        assert len(registered_tools) == 1
        assert registered_tools[0].identifier == "local:guillotine_safe_fetch"

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


@pytest.mark.asyncio
async def test_lifespan_registers_file_tools_only_with_explicit_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("GUILLOTINE_FILE_ROOT", str(tmp_path.resolve()))
    memory = Mock()
    memory.initialize = AsyncMock()
    captured: list[tuple[str, ...]] = []

    def capture_agent(
        _model: object, *, registry: ToolRegistry, executor: ToolExecutor
    ) -> Mock:
        assert isinstance(executor, ToolExecutor)
        captured.append(tuple(entry.identifier for entry in registry.list_tools()))
        return Mock()

    monkeypatch.setattr(
        lifecycle, "router_lifecycle", Mock(return_value=make_async_context(Mock()))
    )
    monkeypatch.setattr(
        lifecycle, "model_lifecycle", Mock(return_value=make_async_context(Mock()))
    )
    monkeypatch.setattr(lifecycle, "MemoryManager", Mock(return_value=memory))
    monkeypatch.setattr(
        lifecycle, "get_checkpointer", Mock(return_value=make_async_context(Mock()))
    )
    monkeypatch.setattr(lifecycle, "create_agent", capture_agent)
    monkeypatch.setattr(lifecycle, "build_workflow", Mock())
    monkeypatch.setattr(lifecycle, "ConversationService", Mock())
    async with lifecycle.lifespan():
        pass
    assert captured == [
        (
            "local:guillotine_safe_fetch",
            "local:list_directory",
            "local:read_file",
            "local:search_files",
        )
    ]

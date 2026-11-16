from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import CompiledStateGraph

from guillotine.core.graph import AgentState
from guillotine.memory.manager import MemoryManager
from guillotine.services.conversations import ConversationService


def build_service() -> tuple[
    ConversationService,
    MagicMock,
    MagicMock,
    MagicMock,
]:
    memory = MagicMock()
    memory.create_conversation = AsyncMock()
    memory.get_conversation = AsyncMock()
    memory.get_history = AsyncMock()
    memory.update_conversation_title = AsyncMock()
    memory.delete_conversation = AsyncMock()
    memory.list_conversations = AsyncMock()

    workflow = MagicMock()
    workflow.ainvoke = AsyncMock()

    checkpointer = MagicMock()
    checkpointer.adelete_thread = AsyncMock()

    service = ConversationService(
        cast(MemoryManager, memory),
        cast(
            CompiledStateGraph[AgentState, None, AgentState, AgentState],
            workflow,
        ),
        cast(AsyncSqliteSaver, checkpointer),
    )

    return service, memory, workflow, checkpointer


async def test_create_conversation() -> None:
    service, memory, _, _ = build_service()
    memory.create_conversation.return_value = "conversation-123"

    result = await service.create("Nova conversa")

    assert result == "conversation-123"
    memory.create_conversation.assert_awaited_once_with("Nova conversa")


async def test_send_first_message_updates_title() -> None:
    service, memory, workflow, _ = build_service()

    memory.get_conversation.return_value = {
        "id": "conversation-123",
        "title": "Nova conversa",
        "created_at": "2026-11-10",
        "updated_at": "2026-11-10",
    }
    memory.get_history.return_value = []
    workflow.ainvoke.return_value = {"response": "Olá, Guilherme!"}

    result = await service.send_message(
        "conversation-123",
        "Olá, Guillotine!",
    )

    assert result == "Olá, Guilherme!"

    memory.update_conversation_title.assert_awaited_once_with(
        "conversation-123",
        "Olá, Guillotine!",
    )

    workflow.ainvoke.assert_awaited_once()


async def test_first_message_title_is_limited_to_50_characters() -> None:
    service, memory, _, _ = build_service()

    memory.get_conversation.return_value = {"id": "conversation-123"}
    memory.get_history.return_value = []

    content = "A" * 60

    await service.send_message("conversation-123", content)

    memory.update_conversation_title.assert_awaited_once_with(
        "conversation-123",
        "A" * 50,
    )


async def test_empty_first_message_is_rejected() -> None:
    service, memory, _, _ = build_service()

    memory.get_conversation.return_value = {"id": "conversation-123"}
    memory.get_history.return_value = []

    with pytest.raises(
        ValueError,
        match="A mensagem não pode estar vazia.",
    ):
        await service.send_message("conversation-123", "   \n ")

    memory.update_conversation_title.assert_not_called()


async def test_send_message_does_not_update_existing_title() -> None:
    service, memory, workflow, _ = build_service()

    memory.get_conversation.return_value = {"id": "conversation-123"}
    memory.get_history.return_value = [
        {
            "id": 1,
            "conversation_id": "conversation-123",
            "role": "user",
            "content": "Mensagem anterior",
            "created_at": "2026-11-10",
        }
    ]
    workflow.ainvoke.return_value = {"response": "Resposta"}

    result = await service.send_message(
        "conversation-123",
        "Nova mensagem",
    )

    assert result == "Resposta"
    memory.update_conversation_title.assert_not_awaited()


async def test_send_message_uses_conversation_id_as_thread_id() -> None:
    service, memory, workflow, _ = build_service()

    memory.get_conversation.return_value = {"id": "conversation-123"}
    memory.get_history.return_value = []
    workflow.ainvoke.return_value = {"response": "Resposta"}

    await service.send_message(
        "conversation-123",
        "Olá",
    )

    call_kwargs = workflow.ainvoke.await_args.kwargs
    config = cast(RunnableConfig, call_kwargs["config"])

    configurable = config.get("configurable")

    assert configurable is not None
    assert configurable["thread_id"] == "conversation-123"


async def test_send_message_with_nonexistent_conversation() -> None:
    service, memory, workflow, _ = build_service()
    memory.get_conversation.return_value = None

    with pytest.raises(ValueError, match="Conversa não encontrada"):
        await service.send_message("inexistente", "Olá")

    workflow.ainvoke.assert_not_awaited()
    memory.get_history.assert_not_awaited()


async def test_get_history() -> None:
    service, memory, _, _ = build_service()

    expected_history = [
        {
            "id": 1,
            "conversation_id": "conversation-123",
            "role": "user",
            "content": "Olá",
            "created_at": "2026-11-10",
        }
    ]

    memory.get_conversation.return_value = {"id": "conversation-123"}
    memory.get_history.return_value = expected_history

    result = await service.get_history("conversation-123")

    assert result == expected_history
    memory.get_history.assert_awaited_once_with("conversation-123")


async def test_get_history_with_nonexistent_conversation() -> None:
    service, memory, _, _ = build_service()
    memory.get_conversation.return_value = None

    with pytest.raises(ValueError, match="Conversa não encontrada"):
        await service.get_history("inexistente")

    memory.get_history.assert_not_awaited()


async def test_delete_conversation() -> None:
    service, memory, _, checkpointer = build_service()
    memory.delete_conversation.return_value = True

    result = await service.delete("conversation-123")

    assert result is True
    checkpointer.adelete_thread.assert_awaited_once_with("conversation-123")
    memory.delete_conversation.assert_awaited_once_with("conversation-123")


async def test_list_conversations() -> None:
    service, memory, _, _ = build_service()

    expected = [
        {
            "id": "conversation-123",
            "title": "Teste",
            "created_at": "2026-11-10",
            "updated_at": "2026-11-10",
        }
    ]

    memory.list_conversations.return_value = expected

    result = await service.list()

    assert result == expected
    memory.list_conversations.assert_awaited_once()


async def test_send_first_message_does_not_update_title_on_workflow_failure() -> None:
    service, memory, workflow, _ = build_service()

    memory.get_conversation.return_value = {
        "id": "conversation-123",
        "title": "Nova conversa",
    }
    memory.get_history.return_value = []

    workflow.ainvoke.side_effect = RuntimeError("Falha no modelo")

    with pytest.raises(RuntimeError, match="Falha no modelo"):
        await service.send_message(
            "conversation-123",
            "Minha primeira mensagem",
        )

    memory.update_conversation_title.assert_not_awaited()


async def test_delete_conversation_does_not_delete_memory_on_checkpointer_failure() -> (
    None
):
    service, memory, _, checkpointer = build_service()

    memory.get_conversation.return_value = {"id": "conversation-123"}
    checkpointer.adelete_thread.side_effect = RuntimeError(
        "Falha ao excluir checkpoint",
    )

    with pytest.raises(RuntimeError, match="Falha ao excluir checkpoint"):
        await service.delete("conversation-123")

    checkpointer.adelete_thread.assert_awaited_once_with("conversation-123")
    memory.delete_conversation.assert_not_awaited()


async def test_delete_nonexistent_conversation() -> None:
    service, memory, _, checkpointer = build_service()

    memory.get_conversation.return_value = None

    result = await service.delete("inexistente")

    assert result is False

    checkpointer.adelete_thread.assert_not_awaited()
    memory.delete_conversation.assert_not_awaited()

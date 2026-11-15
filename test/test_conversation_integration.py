from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, Mock

import pytest
from langchain_core.runnables import RunnableConfig
from pydantic_ai import Agent

from guillotine.core.checkpoint import get_checkpointer
from guillotine.core.graph import build_workflow
from guillotine.memory.manager import MemoryManager
from guillotine.services.conversations import ConversationService


@pytest.mark.integration
async def test_conversation_roundtrip_with_sqlite_and_langgraph(
    test_database_path: Path,
) -> None:
    """Persiste dois turnos, restaura histórico e remove estado/checkpoints."""
    assert not test_database_path.exists()

    memory = MemoryManager()
    await memory.initialize()

    run = AsyncMock(
        side_effect=[
            SimpleNamespace(output="Primeira resposta"),
            SimpleNamespace(output="Segunda resposta"),
        ]
    )
    agent = cast(Agent[None, str], Mock(run=run))

    async with get_checkpointer() as checkpointer:
        workflow = build_workflow(memory, checkpointer, agent)
        service = ConversationService(memory, workflow, checkpointer)
        conversation_id = await service.create("Nova conversa")

        assert await service.send_message(conversation_id, "  Olá, Guillotine!  ") == (
            "Primeira resposta"
        )
        assert await service.send_message(conversation_id, "E agora?") == (
            "Segunda resposta"
        )

        history = await service.get_history(conversation_id)
        assert [(message["role"], message["content"]) for message in history] == [
            ("user", "  Olá, Guillotine!  "),
            ("assistant", "Primeira resposta"),
            ("user", "E agora?"),
            ("assistant", "Segunda resposta"),
        ]

        persisted = await MemoryManager().get_conversation(conversation_id)
        assert persisted is not None
        assert persisted["title"] == "Olá, Guillotine!"
        assert len(await service.list()) == 1

        assert run.await_count == 2
        first_history = run.await_args_list[0].kwargs["message_history"]
        second_history = run.await_args_list[1].kwargs["message_history"]
        assert first_history == []
        assert len(second_history) == 2

        thread_config: RunnableConfig = {"configurable": {"thread_id": conversation_id}}
        assert await checkpointer.aget_tuple(thread_config) is not None

        assert await service.delete(conversation_id) is True
        assert await MemoryManager().get_conversation(conversation_id) is None
        assert await MemoryManager().get_history(conversation_id) == []
        assert await checkpointer.aget_tuple(thread_config) is None

    assert test_database_path.exists()


@pytest.mark.integration
async def test_agent_failure_does_not_persist_exchange_or_change_title(
    test_database_path: Path,
) -> None:
    """Uma falha do modelo não deve gravar mensagens nem alterar o título."""
    memory = MemoryManager()
    await memory.initialize()

    run = AsyncMock(side_effect=RuntimeError("Falha simulada do modelo"))
    agent = cast(Agent[None, str], Mock(run=run))

    async with get_checkpointer() as checkpointer:
        workflow = build_workflow(memory, checkpointer, agent)
        service = ConversationService(memory, workflow, checkpointer)
        conversation_id = await service.create("Nova conversa")

        with pytest.raises(RuntimeError, match="Falha simulada do modelo"):
            await service.send_message(conversation_id, "Mensagem original")

        assert await service.get_history(conversation_id) == []
        persisted = await memory.get_conversation(conversation_id)
        assert persisted is not None
        assert persisted["title"] == "Nova conversa"
        run.assert_awaited_once()

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic_ai.messages import TextPart, UserPromptPart

from guillotine.core import graph
from guillotine.core.checkpoint import get_checkpointer
from guillotine.core.graph import AgentState, build_message_history
from guillotine.memory.manager import MemoryManager
from guillotine.memory.repositories.messages import Message


def make_message(
    role: str,
    content: str,
    message_id: int = 1,
) -> Message:
    return cast(
        Message,
        {
            "id": message_id,
            "conversation_id": "conversation-123",
            "role": role,
            "content": content,
            "created_at": "2026-11-10",
        },
    )


def make_state(conversation_id: str) -> AgentState:
    return {
        "conversation_id": conversation_id,
        "user_input": "Olá, Guillotine!",
        "response": "",
    }


def make_agent_mock() -> MagicMock:
    mocked_agent = MagicMock()
    mocked_agent.run = AsyncMock(
        return_value=SimpleNamespace(output="Olá! Como posso ajudar?")
    )
    return mocked_agent


def test_build_message_history() -> None:
    messages = [
        make_message("user", "Olá", 1),
        make_message("assistant", "Oi!", 2),
        make_message("system", "Instrução interna", 3),
        make_message("tool", "Resultado da ferramenta", 4),
    ]

    history = build_message_history(messages)

    assert len(history) == 2

    user_part = history[0].parts[0]
    assistant_part = history[1].parts[0]

    assert isinstance(user_part, UserPromptPart)
    assert isinstance(assistant_part, TextPart)

    assert user_part.content == "Olá"
    assert assistant_part.content == "Oi!"


def test_build_empty_message_history() -> None:
    history = build_message_history([])

    assert history == []


async def test_workflow_executes_agent_and_persists_messages(
    test_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory = MemoryManager()
    await memory.initialize()

    conversation_id = await memory.create_conversation("Teste")

    mocked_agent = make_agent_mock()

    async with get_checkpointer() as checkpointer:
        workflow = graph.build_workflow(
            memory,
            checkpointer,
            mocked_agent,
        )
        workflow_runner = cast(Any, workflow)

        result = await workflow_runner.ainvoke(
            make_state(conversation_id),
            config={"configurable": {"thread_id": conversation_id}},
        )

    assert result["response"] == "Olá! Como posso ajudar?"

    mocked_agent.run.assert_awaited_once()

    history = await memory.get_history(conversation_id)

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Olá, Guillotine!"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Olá! Como posso ajudar?"


async def test_workflow_passes_previous_history_to_agent(
    test_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory = MemoryManager()
    await memory.initialize()

    conversation_id = await memory.create_conversation("Teste")

    await memory.add_message(
        conversation_id,
        "user",
        "Meu nome é Guilherme.",
    )
    await memory.add_message(
        conversation_id,
        "assistant",
        "Prazer, Guilherme!",
    )

    mocked_agent = make_agent_mock()

    async with get_checkpointer() as checkpointer:
        workflow = graph.build_workflow(
            memory,
            checkpointer,
            mocked_agent,
        )
        workflow_runner = cast(Any, workflow)

        await workflow_runner.ainvoke(
            make_state(conversation_id),
            config={"configurable": {"thread_id": conversation_id}},
        )

    mocked_agent.run.assert_awaited_once()

    call_kwargs = mocked_agent.run.await_args.kwargs
    message_history = call_kwargs["message_history"]

    assert len(message_history) == 2
    assert message_history[0].parts[0].content == "Meu nome é Guilherme."
    assert message_history[1].parts[0].content == "Prazer, Guilherme!"

    history = await memory.get_history(conversation_id)

    assert len(history) == 4


async def test_workflow_uses_current_user_input(
    test_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory = MemoryManager()
    await memory.initialize()

    conversation_id = await memory.create_conversation("Teste")

    mocked_agent = make_agent_mock()

    async with get_checkpointer() as checkpointer:
        workflow = graph.build_workflow(
            memory,
            checkpointer,
            mocked_agent,
        )
        workflow_runner = cast(Any, workflow)

        await workflow_runner.ainvoke(
            {
                "conversation_id": conversation_id,
                "user_input": "Qual é a capital do Brasil?",
                "response": "",
            },
            config={"configurable": {"thread_id": conversation_id}},
        )

    mocked_agent.run.assert_awaited_once()

    call_args = mocked_agent.run.await_args

    assert call_args.args[0] == "Qual é a capital do Brasil?"

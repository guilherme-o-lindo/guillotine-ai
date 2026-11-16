import sqlite3
from pathlib import Path

import pytest

from guillotine.memory.repositories import conversations, messages
from guillotine.memory.storage import database


async def test_create_and_get_message(test_database_path: Path) -> None:
    await database.initialize_database()

    conversation_id = await conversations.create_conversation("Teste")

    message_id = await messages.create_message(
        conversation_id,
        "user",
        "Olá, Guillotine!",
    )

    message = await messages.get_message(message_id)

    assert message is not None
    assert message["id"] == message_id
    assert message["conversation_id"] == conversation_id
    assert message["role"] == "user"
    assert message["content"] == "Olá, Guillotine!"


async def test_get_nonexistent_message(test_database_path: Path) -> None:
    await database.initialize_database()

    message = await messages.get_message(-1)

    assert message is None


async def test_list_messages(test_database_path: Path) -> None:
    await database.initialize_database()

    conversation_id = await conversations.create_conversation("Teste")

    first_id = await messages.create_message(
        conversation_id,
        "user",
        "Primeira mensagem",
    )

    second_id = await messages.create_message(
        conversation_id,
        "assistant",
        "Segunda mensagem",
    )

    result = await messages.list_messages(conversation_id)

    assert len(result) == 2
    assert result[0]["id"] == first_id
    assert result[1]["id"] == second_id


async def test_delete_message(test_database_path: Path) -> None:
    await database.initialize_database()

    conversation_id = await conversations.create_conversation("Teste")

    message_id = await messages.create_message(
        conversation_id,
        "user",
        "Mensagem para excluir",
    )

    deleted = await messages.delete_message(message_id)

    message = await messages.get_message(message_id)

    assert deleted is True
    assert message is None


async def test_delete_nonexistent_message(test_database_path: Path) -> None:
    await database.initialize_database()

    deleted = await messages.delete_message(-1)

    assert deleted is False


async def test_delete_conversation_cascades_messages(
    test_database_path: Path,
) -> None:
    await database.initialize_database()

    conversation_id = await conversations.create_conversation("Teste")

    await messages.create_message(
        conversation_id,
        "user",
        "Mensagem 1",
    )

    await messages.create_message(
        conversation_id,
        "assistant",
        "Mensagem 2",
    )

    deleted = await conversations.delete_conversation(conversation_id)

    remaining_messages = await messages.list_messages(conversation_id)

    assert deleted is True
    assert remaining_messages == []


async def test_create_message_with_invalid_conversation(
    test_database_path: Path,
) -> None:
    await database.initialize_database()

    with pytest.raises(sqlite3.IntegrityError):
        await messages.create_message(
            "conversa-inexistente",
            "user",
            "Esta mensagem não deveria ser salva",
        )


async def test_create_exchange(test_database_path: Path) -> None:
    await database.initialize_database()

    conversation_id = await conversations.create_conversation("Teste")

    user_id, assistant_id = await messages.create_exchange(
        conversation_id,
        "Olá, Guillotine!",
        "Olá! Como posso ajudar?",
    )

    history = await messages.list_messages(conversation_id)

    assert len(history) == 2

    assert history[0]["id"] == user_id
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Olá, Guillotine!"

    assert history[1]["id"] == assistant_id
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Olá! Como posso ajudar?"


async def test_create_exchange_rolls_back_on_failure(
    test_database_path: Path,
) -> None:
    await database.initialize_database()

    conversation_id = await conversations.create_conversation("Teste")

    async with database.get_connection() as connection:
        await connection.execute(
            """
            CREATE TRIGGER fail_assistant_insert
            BEFORE INSERT ON messages
            WHEN NEW.role = 'assistant'
            BEGIN
                SELECT RAISE(ABORT, 'Falha simulada');
            END;
            """
        )
        await connection.commit()

    with pytest.raises(sqlite3.IntegrityError):
        await messages.create_exchange(
            conversation_id,
            "Mensagem do usuário",
            "Resposta do assistente",
        )

    history = await messages.list_messages(conversation_id)

    assert history == []

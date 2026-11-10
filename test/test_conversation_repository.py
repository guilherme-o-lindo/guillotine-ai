from pathlib import Path

from guillotine.memory.repositories import conversations
from guillotine.memory.storage import database


async def test_create_conversation(test_database_path: Path) -> None:
    await database.initialize_database()

    conversation_id = await conversations.create_conversation("Nova conversa")

    conversation = await conversations.get_conversation(conversation_id)

    assert conversation is not None
    assert conversation["id"] == conversation_id
    assert conversation["title"] == "Nova conversa"


async def test_get_nonexistent_conversation(test_database_path: Path) -> None:
    await database.initialize_database()

    conversation = await conversations.get_conversation("inexistente")

    assert conversation is None


async def test_list_conversations(test_database_path: Path) -> None:
    await database.initialize_database()

    first_id = await conversations.create_conversation("Primeira")
    second_id = await conversations.create_conversation("Segunda")

    result = await conversations.list_conversations()

    conversation_ids = {conversation["id"] for conversation in result}

    assert len(result) == 2
    assert first_id in conversation_ids
    assert second_id in conversation_ids


async def test_update_conversation_title(test_database_path: Path) -> None:
    await database.initialize_database()

    conversation_id = await conversations.create_conversation("Título original")

    updated = await conversations.update_conversation_title(
        conversation_id,
        "Título atualizado",
    )

    conversation = await conversations.get_conversation(conversation_id)

    assert updated is True
    assert conversation is not None
    assert conversation["title"] == "Título atualizado"


async def test_delete_conversation(test_database_path: Path) -> None:
    await database.initialize_database()

    conversation_id = await conversations.create_conversation("Para excluir")

    deleted = await conversations.delete_conversation(conversation_id)

    conversation = await conversations.get_conversation(conversation_id)

    assert deleted is True
    assert conversation is None


async def test_update_nonexistent_conversation(test_database_path: Path) -> None:
    await database.initialize_database()

    updated = await conversations.update_conversation_title(
        "inexistente",
        "Novo título",
    )

    assert updated is False


async def test_delete_nonexistent_conversation(test_database_path: Path) -> None:
    await database.initialize_database()

    deleted = await conversations.delete_conversation("inexistente")

    assert deleted is False


async def test_delete_conversation_cascades_messages(
    test_database_path: Path,
) -> None:
    await database.initialize_database()

    conversation_id = await conversations.create_conversation(
        "Conversa com mensagens",
    )

    async with database.get_connection() as connection:
        await connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, "user", "Mensagem de teste"),
        )
        await connection.commit()

    deleted = await conversations.delete_conversation(conversation_id)

    async with (
        database.get_connection() as connection,
        connection.execute(
            """
            SELECT id
            FROM messages
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        ) as cursor,
    ):
        messages = await cursor.fetchall()

    assert deleted is True
    assert messages == []

from typing import TypedDict
from uuid import uuid4

from guillotine.memory.storage.database import get_connection


class Conversation(TypedDict):
    id: str
    title: str
    created_at: str
    updated_at: str


async def create_conversation(title: str) -> str:
    conversation_id = str(uuid4())

    async with get_connection() as database:
        await database.execute(
            """
            INSERT INTO conversations (id, title)
            VALUES (?, ?)
            """,
            (conversation_id, title),
        )

        await database.commit()

    return conversation_id


async def get_conversation(
    conversation_id: str,
) -> Conversation | None:
    async with (
        get_connection() as database,
        database.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        ) as cursor,
    ):
        row = await cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


async def list_conversations() -> list[Conversation]:
    async with (
        get_connection() as database,
        database.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC
            """
        ) as cursor,
    ):
        rows = await cursor.fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]


async def delete_conversation(conversation_id: str) -> bool:
    async with get_connection() as database:
        async with database.execute(
            """
            DELETE FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        ) as cursor:
            deleted = cursor.rowcount > 0

        await database.commit()

        return deleted


async def update_conversation_title(
    conversation_id: str,
    title: str,
) -> bool:
    async with get_connection() as database:
        async with database.execute(
            """
            UPDATE conversations
            SET title = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, conversation_id),
        ) as cursor:
            updated = cursor.rowcount > 0

        await database.commit()

        return updated

from typing import Literal, TypedDict

from guillotine.memory.storage.database import get_connection

MessageRole = Literal["system", "user", "assistant", "tool"]


class Message(TypedDict):
    id: int
    conversation_id: str
    role: MessageRole
    content: str
    created_at: str


async def create_message(
    conversation_id: str,
    role: MessageRole,
    content: str,
) -> int:
    async with get_connection() as database:
        async with database.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content),
        ) as cursor:
            message_id = cursor.lastrowid

        if message_id is None:
            raise RuntimeError("Não foi possível recuperar o ID da mensagem.")

        await database.execute(
            """
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (conversation_id,),
        )

        await database.commit()

        return message_id


async def create_exchange(
    conversation_id: str,
    user_content: str,
    assistant_content: str,
) -> tuple[int, int]:
    async with get_connection() as database:
        try:
            async with database.execute(
                """
                INSERT INTO messages (conversation_id, role, content)
                VALUES (?, 'user', ?)
                """,
                (conversation_id, user_content),
            ) as cursor:
                user_message_id = cursor.lastrowid

            if user_message_id is None:
                raise RuntimeError(
                    "Não foi possível recuperar o ID da mensagem do usuário."
                )

            async with database.execute(
                """
                INSERT INTO messages (conversation_id, role, content)
                VALUES (?, 'assistant', ?)
                """,
                (conversation_id, assistant_content),
            ) as cursor:
                assistant_message_id = cursor.lastrowid

            if assistant_message_id is None:
                raise RuntimeError(
                    "Não foi possível recuperar o ID da resposta do assistente."
                )

            await database.execute(
                """
                UPDATE conversations
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (conversation_id,),
            )

            await database.commit()

            return user_message_id, assistant_message_id

        except Exception:
            await database.rollback()
            raise


async def get_message(message_id: int) -> Message | None:
    async with (
        get_connection() as database,
        database.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE id = ?
            """,
            (message_id,),
        ) as cursor,
    ):
        row = await cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "conversation_id": row["conversation_id"],
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"],
        }


async def list_messages(conversation_id: str) -> list[Message]:
    async with (
        get_connection() as database,
        database.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ) as cursor,
    ):
        rows = await cursor.fetchall()

        return [
            {
                "id": row["id"],
                "conversation_id": row["conversation_id"],
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


async def delete_message(message_id: int) -> bool:
    async with get_connection() as database:
        async with database.execute(
            """
            DELETE FROM messages
            WHERE id = ?
            """,
            (message_id,),
        ) as cursor:
            deleted = cursor.rowcount > 0

        await database.commit()

        return deleted

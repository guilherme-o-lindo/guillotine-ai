from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

ROOT_DIR = Path(__file__).resolve().parents[4]
DATABASE_PATH = ROOT_DIR / "data" / "guillotine.db"


@asynccontextmanager
async def get_connection() -> AsyncGenerator[aiosqlite.Connection, None]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = await aiosqlite.connect(DATABASE_PATH)
    connection.row_factory = aiosqlite.Row

    await connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
    finally:
        await connection.close()


async def initialize_database() -> None:
    async with get_connection() as database:
        await database.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN ('system', 'user', 'assistant', 'tool')
                ),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id);
            """
        )

        await database.commit()

from pathlib import Path

from guillotine.memory.storage import database


async def test_initialize_database_creates_tables(
    test_database_path: Path,
) -> None:
    await database.initialize_database()

    async with (
        database.get_connection() as connection,
        connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ) as cursor,
    ):
        rows = await cursor.fetchall()

    table_names = {row["name"] for row in rows}

    assert "conversations" in table_names
    assert "messages" in table_names


async def test_foreign_keys_are_enabled(
    test_database_path: Path,
) -> None:
    await database.initialize_database()

    async with (
        database.get_connection() as connection,
        connection.execute("PRAGMA foreign_keys") as cursor,
    ):
        result = await cursor.fetchone()

    assert result is not None
    assert result[0] == 1

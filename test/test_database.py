import asyncio

from guillotine.memory.storage.database import (
    get_connection,
    initialize_database,
)


async def main() -> None:
    await initialize_database()

    async with (
        get_connection() as database,
        database.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ) as cursor,
    ):
        rows = await cursor.fetchall()

        for row in rows:
            print(row["name"])


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

from guillotine.core.lifecycle import lifespan
from guillotine.interfaces.cli import run_cli


async def main() -> None:
    async with lifespan() as conversation_service:
        await run_cli(conversation_service)


if __name__ == "__main__":
    asyncio.run(main())

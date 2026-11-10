import asyncio

from guillotine.core.lifecycle import lifespan
from guillotine.interfaces.cli import run_cli


async def run() -> None:
    async with lifespan() as conversation_service:
        await run_cli(conversation_service)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

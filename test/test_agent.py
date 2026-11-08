import asyncio

from guillotine.core.agent import agent


async def main() -> None:
    result = await agent.run("Apresente-se brevemente e diga que está funcionando.")

    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

from guillotine.core.config import settings
from guillotine.models.provider import client


async def main() -> None:
    response = await client.chat.completions.create(
        model=settings.MODEL,
        messages=[
            {
                "role": "user",
                "content": "Responda apenas: conexão estabelecida.",
            }
        ],
    )

    print(response.choices[0].message.content)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())

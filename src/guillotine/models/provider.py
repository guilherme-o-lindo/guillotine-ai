from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx2
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from guillotine.core.config import settings


@asynccontextmanager
async def model_lifecycle() -> AsyncGenerator[OpenAIChatModel, None]:
    async with httpx2.AsyncClient(
        timeout=httpx2.Timeout(
            settings.TIMEOUT_SECONDS,
            connect=10.0,
        ),
    ) as http_client:
        provider = OpenAIProvider(
            base_url=settings.BASE_URL,
            api_key=settings.API_KEY,
            http_client=http_client,
        )

        model = OpenAIChatModel(
            settings.MODEL,
            provider=provider,
        )

        yield model

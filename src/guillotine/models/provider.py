from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from guillotine.core.config import settings

client = AsyncOpenAI(
    base_url=settings.BASE_URL,
    api_key=settings.API_KEY,
)

provider = OpenAIProvider(
    base_url=settings.BASE_URL,
    api_key=settings.API_KEY,
)

model = OpenAIChatModel(
    settings.MODEL,
    provider=provider,
)

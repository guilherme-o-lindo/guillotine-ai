from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from guillotine.core.agent import create_agent
from guillotine.core.checkpoint import get_checkpointer
from guillotine.core.graph import build_workflow
from guillotine.memory.manager import MemoryManager
from guillotine.models.provider import model_lifecycle
from guillotine.models.router import router_lifecycle
from guillotine.services.conversations import ConversationService


@asynccontextmanager
async def lifespan() -> AsyncGenerator[ConversationService, None]:
    async with router_lifecycle(), model_lifecycle() as model:
        memory = MemoryManager()

        await memory.initialize()

        agent = create_agent(model)

        async with get_checkpointer() as checkpointer:
            workflow = build_workflow(
                memory,
                checkpointer,
                agent,
            )

            conversation_service = ConversationService(
                memory,
                workflow,
                checkpointer,
            )

            yield conversation_service

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from guillotine.core.checkpoint import get_checkpointer
from guillotine.core.graph import build_workflow
from guillotine.memory.manager import MemoryManager
from guillotine.services.conversations import ConversationService


@asynccontextmanager
async def lifespan() -> AsyncGenerator[ConversationService, None]:
    memory = MemoryManager()

    await memory.initialize()

    async with get_checkpointer() as checkpointer:
        workflow = build_workflow(memory, checkpointer)

        conversation_service = ConversationService(
            memory,
            workflow,
            checkpointer,
        )

        yield conversation_service

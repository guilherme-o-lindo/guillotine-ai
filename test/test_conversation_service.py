import asyncio

from guillotine.core.checkpoint import get_checkpointer
from guillotine.core.graph import build_workflow
from guillotine.memory.manager import MemoryManager
from guillotine.services.conversations import ConversationService


async def main() -> None:
    memory = MemoryManager()
    await memory.initialize()

    async with get_checkpointer() as checkpointer:
        workflow = build_workflow(memory, checkpointer)

        service = ConversationService(
            memory,
            workflow,
            checkpointer,
        )

        conversation_id = await service.create("Teste do ConversationService")

        print("Conversa criada:", conversation_id)

        first_response = await service.send_message(
            conversation_id,
            "Meu nome é Guilherme.",
        )
        print("\nPrimeira resposta:", first_response)

        second_response = await service.send_message(
            conversation_id,
            "Qual é o meu nome?",
        )
        print("\nSegunda resposta:", second_response)

        history = await service.get_history(conversation_id)

        print("\nHistórico:")
        for message in history:
            print(f"[{message['role']}] {message['content']}")

        await service.delete(conversation_id)
        print("\nConversa removida.")


if __name__ == "__main__":
    asyncio.run(main())

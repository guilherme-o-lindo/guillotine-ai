import asyncio

from guillotine.memory.manager import MemoryManager


async def main() -> None:
    memory = MemoryManager()

    await memory.initialize()

    conversation_id = await memory.create_conversation("Conversa com Guillotine")

    await memory.add_message(
        conversation_id,
        "user",
        "Olá, Guillotine!",
    )

    await memory.add_message(
        conversation_id,
        "assistant",
        "Olá! Como posso ajudar?",
    )

    conversation = await memory.get_conversation(conversation_id)
    print("Conversa:", conversation)

    history = await memory.get_history(conversation_id)

    print("\nHistórico:")
    for message in history:
        print(f"[{message['role']}] {message['content']}")

    conversations = await memory.list_conversations()
    print("\nTotal de conversas:", len(conversations))

    deleted = await memory.delete_conversation(conversation_id)
    print("\nConversa excluída:", deleted)


if __name__ == "__main__":
    asyncio.run(main())

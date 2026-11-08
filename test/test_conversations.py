import asyncio

from guillotine.memory.repositories.conversations import (
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
)
from guillotine.memory.storage.database import initialize_database


async def main() -> None:
    await initialize_database()

    conversation_id = await create_conversation("Conversa de teste")
    print("ID:", conversation_id)

    conversation = await get_conversation(conversation_id)
    print("Conversa:", conversation)

    conversations = await list_conversations()
    print("Total de conversas:", len(conversations))

    deleted = await delete_conversation(conversation_id)
    print("Excluída:", deleted)

    conversation = await get_conversation(conversation_id)
    print("Após exclusão:", conversation)


if __name__ == "__main__":
    asyncio.run(main())

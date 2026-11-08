import asyncio

from guillotine.memory.repositories.conversations import (
    create_conversation,
    delete_conversation,
)
from guillotine.memory.repositories.messages import (
    create_message,
    delete_message,
    get_message,
    list_messages,
)
from guillotine.memory.storage.database import initialize_database


async def main() -> None:
    await initialize_database()

    conversation_id = await create_conversation("Teste de mensagens")

    message_id = await create_message(
        conversation_id,
        "user",
        "Olá, Guillotine!",
    )

    await create_message(
        conversation_id,
        "assistant",
        "Olá! Como posso ajudar?",
    )

    message = await get_message(message_id)
    print("Mensagem:", message)

    messages = await list_messages(conversation_id)
    print("Histórico:")

    for item in messages:
        print(f"[{item['role']}] {item['content']}")

    deleted = await delete_message(message_id)
    print("Mensagem excluída:", deleted)

    remaining_messages = await list_messages(conversation_id)
    print("Mensagens restantes:", len(remaining_messages))

    await delete_conversation(conversation_id)


if __name__ == "__main__":
    asyncio.run(main())

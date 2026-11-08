from guillotine.memory.repositories.conversations import (
    Conversation,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    update_conversation_title,
)
from guillotine.memory.repositories.messages import (
    Message,
    MessageRole,
    create_message,
    delete_message,
    get_message,
    list_messages,
)
from guillotine.memory.storage.database import initialize_database


class MemoryManager:
    async def initialize(self) -> None:
        await initialize_database()

    async def create_conversation(self, title: str) -> str:
        return await create_conversation(title)

    async def get_conversation(
        self,
        conversation_id: str,
    ) -> Conversation | None:
        return await get_conversation(conversation_id)

    async def list_conversations(self) -> list[Conversation]:
        return await list_conversations()

    async def delete_conversation(self, conversation_id: str) -> bool:
        return await delete_conversation(conversation_id)

    async def add_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
    ) -> int:
        return await create_message(conversation_id, role, content)

    async def get_message(self, message_id: int) -> Message | None:
        return await get_message(message_id)

    async def get_history(self, conversation_id: str) -> list[Message]:
        return await list_messages(conversation_id)

    async def delete_message(self, message_id: int) -> bool:
        return await delete_message(message_id)

    async def update_conversation_title(
        self,
        conversation_id: str,
        title: str,
    ) -> bool:
        return await update_conversation_title(
            conversation_id,
            title,
        )

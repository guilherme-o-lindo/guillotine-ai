from typing import cast

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import CompiledStateGraph

from guillotine.core.graph import AgentState
from guillotine.memory.manager import MemoryManager
from guillotine.memory.repositories.conversations import Conversation
from guillotine.memory.repositories.messages import Message


class ConversationService:
    def __init__(
        self,
        memory: MemoryManager,
        workflow: CompiledStateGraph[AgentState, None, AgentState, AgentState],
        checkpointer: AsyncSqliteSaver,
    ) -> None:
        self.memory = memory
        self.workflow = workflow
        self.checkpointer = checkpointer

    async def create(self, title: str) -> str:
        return await self.memory.create_conversation(title)

    async def send_message(
        self,
        conversation_id: str,
        content: str,
    ) -> str:
        conversation = await self.memory.get_conversation(conversation_id)

        if conversation is None:
            raise ValueError("Conversa não encontrada.")

        history = await self.memory.get_history(conversation_id)

        if not history:
            title = content.strip().replace("\n", " ")[:50]

            await self.memory.update_conversation_title(
                conversation_id,
                title or "Nova conversa",
            )

        config: RunnableConfig = {
            "configurable": {
                "thread_id": conversation_id,
            }
        }

        initial_state: AgentState = {
            "conversation_id": conversation_id,
            "user_input": content,
            "response": "",
        }

        result = cast(
            AgentState,
            await self.workflow.ainvoke(  # pyright: ignore[reportUnknownMemberType]
                initial_state,
                config=config,
            ),
        )

        return result["response"]

    async def get_history(
        self,
        conversation_id: str,
    ) -> list[Message]:
        conversation = await self.memory.get_conversation(conversation_id)

        if conversation is None:
            raise ValueError("Conversa não encontrada.")

        return await self.memory.get_history(conversation_id)

    async def delete(self, conversation_id: str) -> bool:
        await self.checkpointer.adelete_thread(conversation_id)

        return await self.memory.delete_conversation(conversation_id)

    async def list(self) -> list[Conversation]:
        return await self.memory.list_conversations()

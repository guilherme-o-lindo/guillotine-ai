import asyncio
from typing import cast

from langchain_core.runnables import RunnableConfig

from guillotine.core.checkpoint import get_checkpointer
from guillotine.core.graph import AgentState, build_workflow
from guillotine.memory.manager import MemoryManager


async def main() -> None:
    memory = MemoryManager()

    await memory.initialize()

    conversation_id = await memory.create_conversation("Teste de checkpoints")

    config: RunnableConfig = {
        "configurable": {
            "thread_id": conversation_id,
        }
    }

    async with get_checkpointer() as checkpointer:
        workflow = build_workflow(memory, checkpointer)

        initial_state: AgentState = {
            "conversation_id": conversation_id,
            "user_input": "Meu nome é Guilherme.",
            "response": "",
        }

        first_result = cast(
            AgentState,
            await workflow.ainvoke(  # pyright: ignore[reportUnknownMemberType]
                initial_state,
                config=config,
            ),
        )

        print("Primeira resposta:", first_result["response"])

        second_state: AgentState = {
            "conversation_id": conversation_id,
            "user_input": "Qual é o meu nome?",
            "response": "",
        }

        second_result = cast(
            AgentState,
            await workflow.ainvoke(  # pyright: ignore[reportUnknownMemberType]
                second_state,
                config=config,
            ),
        )

        print("\nSegunda resposta:", second_result["response"])

        snapshot = await workflow.aget_state(config)  # pyright: ignore[reportUnknownMemberType]

        print("\nEstado persistido no LangGraph:")
        print(snapshot.values)

        history = await memory.get_history(conversation_id)

        print("\nHistórico no SQLite:")

        for message in history:
            print(f"[{message['role']}] {message['content']}")

        await checkpointer.adelete_thread(conversation_id)

    await memory.delete_conversation(conversation_id)


if __name__ == "__main__":
    asyncio.run(main())

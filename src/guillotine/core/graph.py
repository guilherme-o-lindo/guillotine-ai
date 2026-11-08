from typing import TypedDict

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from guillotine.core.agent import agent
from guillotine.memory.manager import MemoryManager
from guillotine.memory.repositories.messages import Message


class AgentState(TypedDict):
    conversation_id: str
    user_input: str
    response: str


def build_message_history(messages: list[Message]) -> list[ModelMessage]:
    history: list[ModelMessage] = []

    for message in messages:
        if message["role"] == "user":
            history.append(
                ModelRequest(
                    parts=[
                        UserPromptPart(content=message["content"]),
                    ],
                )
            )

        elif message["role"] == "assistant":
            history.append(
                ModelResponse(
                    parts=[
                        TextPart(content=message["content"]),
                    ],
                )
            )

    return history


def build_workflow(
    memory: MemoryManager,
    checkpointer: AsyncSqliteSaver,
) -> CompiledStateGraph[AgentState, None, AgentState, AgentState]:

    async def run_agent(state: AgentState) -> dict[str, str]:
        conversation_id = state["conversation_id"]

        previous_messages = await memory.get_history(conversation_id)
        message_history = build_message_history(previous_messages)

        result = await agent.run(
            state["user_input"],
            message_history=message_history,
        )

        response = result.output

        await memory.add_message(
            conversation_id,
            "user",
            state["user_input"],
        )

        await memory.add_message(
            conversation_id,
            "assistant",
            response,
        )

        return {"response": response}

    builder = StateGraph(AgentState)

    builder.add_node(  # pyright: ignore[reportUnknownMemberType]
        "agent",
        run_agent,
    )

    builder.add_edge(START, "agent")
    builder.add_edge("agent", END)

    return builder.compile(  # pyright: ignore[reportUnknownMemberType]
        checkpointer=checkpointer,
    )

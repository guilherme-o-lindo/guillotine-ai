"""Construct the PydanticAI agent; tool access is opt-in and always guarded."""

from pydantic_ai import Agent
from pydantic_ai.models import Model

from guillotine.tools.bridges.pydantic_ai import (
    attach_executor_tool,
    tool_catalog,
    visible_tools,
)
from guillotine.tools.core.executor import ToolExecutor
from guillotine.tools.core.registry import ToolRegistry

INSTRUCTIONS = (
    "Você é Guillotine, um assistente de IA pessoal. "
    "Responda de maneira clara, útil e objetiva."
)


def create_agent(
    model: Model,
    *,
    registry: ToolRegistry | None = None,
    executor: ToolExecutor | None = None,
) -> Agent[None, str]:
    """Only expose tools when both registry and authorized executor are given."""
    if (registry is None) != (executor is None):
        raise ValueError("Registry e Executor devem ser configurados juntos")

    instructions = INSTRUCTIONS
    if registry is not None and executor is not None:
        entries = visible_tools(registry)
        if entries:
            instructions += "\n" + tool_catalog(entries)

    agent: Agent[None, str] = Agent(model, instructions=instructions)
    if registry is not None and executor is not None:
        attach_executor_tool(agent, registry, executor)
    return agent

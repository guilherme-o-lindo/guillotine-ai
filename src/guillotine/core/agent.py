from pydantic_ai import Agent
from pydantic_ai.models import Model

INSTRUCTIONS = (
    "Você é Guillotine, um assistente de IA pessoal. "
    "Responda de maneira clara, útil e objetiva."
)


def create_agent(model: Model) -> Agent[None, str]:
    return Agent(
        model,
        instructions=INSTRUCTIONS,
    )

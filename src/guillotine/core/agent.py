from pydantic_ai import Agent

from guillotine.models.provider import model

agent = Agent(
    model,
    instructions=(
        "Você é Guillotine, um assistente de IA pessoal. "
        "Responda de maneira clara, útil e objetiva."
    ),
)

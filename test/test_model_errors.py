import pytest
from pydantic_ai.exceptions import (
    ModelAPIError,
    ModelAuthenticationError,
    ModelConnectionError,
    ModelContextWindowExceededError,
    ModelNotFoundError,
    ModelOverloadedError,
    ModelQuotaExceededError,
    ModelRateLimitError,
    ModelServerError,
    ModelTimeoutError,
    ModelUnavailableError,
)

from guillotine.models.errors import get_model_error_message


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            ModelTimeoutError("test-model", "timeout"),
            "O modelo demorou demais para responder. Tente novamente.",
        ),
        (
            ModelAuthenticationError("test-model", "unauthorized"),
            "Falha de autenticação. Verifique as credenciais do provedor.",
        ),
        (
            ModelNotFoundError("test-model", "not found"),
            "O modelo configurado não foi encontrado. Verifique seu nome.",
        ),
        (
            ModelContextWindowExceededError("test-model", "context exceeded"),
            "A conversa excedeu o limite de contexto do modelo.",
        ),
        (
            ModelQuotaExceededError("test-model", "quota exceeded"),
            "A cota de utilização do provedor foi excedida.",
        ),
        (
            ModelRateLimitError("test-model", "rate limited"),
            "Limite de requisições atingido. Aguarde antes de tentar novamente.",
        ),
        (
            ModelOverloadedError("test-model", "overloaded"),
            "O provedor está sobrecarregado. Tente novamente mais tarde.",
        ),
        (
            ModelConnectionError("test-model", "connection failed"),
            "Não foi possível estabelecer conexão com o provedor.",
        ),
        (
            ModelServerError("test-model", "server error"),
            "O servidor do provedor apresentou um erro.",
        ),
        (
            ModelUnavailableError("test-model", "unavailable"),
            "O serviço do modelo está temporariamente indisponível.",
        ),
        (
            ModelAPIError("test-model", "unknown error"),
            "Ocorreu um erro ao solicitar uma resposta ao modelo.",
        ),
    ],
)
def test_get_model_error_message(
    error: ModelAPIError,
    expected: str,
) -> None:
    assert get_model_error_message(error) == expected

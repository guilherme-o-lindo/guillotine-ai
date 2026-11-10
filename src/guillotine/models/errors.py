from pydantic_ai.exceptions import (
    ModelAPIError,
    ModelAuthenticationError,
    ModelConnectionError,
    ModelContextWindowExceededError,
    ModelHTTPError,
    ModelNotFoundError,
    ModelOverloadedError,
    ModelQuotaExceededError,
    ModelRateLimitError,
    ModelRequestRejectedError,
    ModelServerError,
    ModelTimeoutError,
    ModelUnavailableError,
)


def get_model_error_message(error: ModelAPIError) -> str:
    if isinstance(error, ModelTimeoutError):
        return "O modelo demorou demais para responder. Tente novamente."

    if isinstance(error, ModelAuthenticationError):
        return "Falha de autenticação. Verifique as credenciais do provedor."

    if isinstance(error, ModelNotFoundError):
        return "O modelo configurado não foi encontrado. Verifique seu nome."

    if isinstance(error, ModelContextWindowExceededError):
        return "A conversa excedeu o limite de contexto do modelo."

    if isinstance(error, ModelQuotaExceededError):
        return "A cota de utilização do provedor foi excedida."

    if isinstance(error, ModelRateLimitError):
        return "Limite de requisições atingido. Aguarde antes de tentar novamente."

    if isinstance(error, ModelOverloadedError):
        return "O provedor está sobrecarregado. Tente novamente mais tarde."

    if isinstance(error, ModelConnectionError):
        return "Não foi possível estabelecer conexão com o provedor."

    if isinstance(error, ModelServerError):
        return "O servidor do provedor apresentou um erro."

    if isinstance(error, ModelUnavailableError):
        return "O serviço do modelo está temporariamente indisponível."

    if isinstance(error, ModelRequestRejectedError):
        return "O provedor recusou a solicitação."

    if isinstance(error, ModelHTTPError):
        return f"O provedor retornou um erro HTTP ({error.status_code})."

    return "Ocorreu um erro ao solicitar uma resposta ao modelo."

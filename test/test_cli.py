import builtins
from datetime import UTC, datetime
from typing import cast

import pytest
from pydantic_ai.exceptions import ModelTimeoutError

from guillotine.interfaces.cli import run_cli
from guillotine.memory.repositories.conversations import Conversation
from guillotine.memory.repositories.messages import Message
from guillotine.services.conversations import ConversationService


class FakeConversationService:
    def __init__(self) -> None:
        self.created_titles: builtins.list[str] = []
        self.deleted_ids: builtins.list[str] = []
        self.sent_messages: builtins.list[tuple[str, str]] = []
        self.conversations: builtins.list[Conversation] = []
        self.histories: dict[str, builtins.list[Message]] = {}
        self.delete_result = True
        self.response = "Resposta simulada."
        self.send_message_error: Exception | None = None

    async def create(self, title: str) -> str:
        self.created_titles.append(title)
        return f"conversation-{len(self.created_titles)}"

    async def list(self) -> builtins.list[Conversation]:
        return self.conversations

    async def get_history(
        self,
        conversation_id: str,
    ) -> builtins.list[Message]:
        return self.histories.get(conversation_id, [])

    async def delete(self, conversation_id: str) -> bool:
        self.deleted_ids.append(conversation_id)
        return self.delete_result

    async def send_message(
        self,
        conversation_id: str,
        content: str,
    ) -> str:
        self.sent_messages.append((conversation_id, content))

        if self.send_message_error is not None:
            error = self.send_message_error
            self.send_message_error = None
            raise error

        return self.response


@pytest.fixture
def service() -> FakeConversationService:
    return FakeConversationService()


def set_cli_inputs(
    monkeypatch: pytest.MonkeyPatch,
    inputs: builtins.list[str],
) -> None:
    input_iterator = iter(inputs)

    def mock_input(_: str) -> str:
        return next(input_iterator)

    monkeypatch.setattr("builtins.input", mock_input)


def create_fake_message(role: str, content: str) -> Message:
    return cast(
        Message,
        {
            "role": role,
            "content": content,
        },
    )


def create_fake_conversation(
    conversation_id: str,
    title: str,
) -> Conversation:
    return cast(
        Conversation,
        {
            "id": conversation_id,
            "title": title,
            "updated_at": datetime.now(UTC).isoformat(),
        },
    )


@pytest.mark.asyncio
async def test_cli_exits(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    set_cli_inputs(monkeypatch, ["/sair"])

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert "Guillotine iniciado." in output
    assert "Guillotine encerrado." in output


@pytest.mark.asyncio
async def test_cli_displays_help(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    set_cli_inputs(monkeypatch, ["/ajuda", "/sair"])

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert "/nova" in output
    assert "/conversas" in output
    assert "/historico" in output
    assert "/excluir" in output


@pytest.mark.asyncio
async def test_cli_creates_new_conversation(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_cli_inputs(monkeypatch, ["/nova", "/sair"])

    await run_cli(cast(ConversationService, service))

    assert service.created_titles == [
        "Nova conversa",
        "Nova conversa",
    ]


@pytest.mark.asyncio
async def test_cli_does_not_send_unknown_commands(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    set_cli_inputs(
        monkeypatch,
        ["/comando-inexistente", "/sair"],
    )

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert "Comando não reconhecido." in output
    assert service.sent_messages == []


@pytest.mark.asyncio
async def test_cli_sends_regular_messages(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    set_cli_inputs(
        monkeypatch,
        ["Olá, Guillotine!", "/sair"],
    )

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert service.sent_messages == [("conversation-1", "Olá, Guillotine!")]
    assert "Resposta simulada." in output


@pytest.mark.asyncio
async def test_cli_deletes_conversation_and_creates_another(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    set_cli_inputs(monkeypatch, ["/excluir", "/sair"])

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert service.deleted_ids == ["conversation-1"]
    assert len(service.created_titles) == 2
    assert "Conversa excluída." in output


@pytest.mark.asyncio
async def test_cli_does_not_create_conversation_when_delete_fails(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service.delete_result = False

    set_cli_inputs(monkeypatch, ["/excluir", "/sair"])

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert len(service.created_titles) == 1
    assert "Conversa não encontrada." in output
    assert "Conversa excluída." not in output


@pytest.mark.asyncio
async def test_cli_lists_conversations(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service.conversations = [
        create_fake_conversation("conversation-1", "Primeira conversa"),
        create_fake_conversation("conversation-2", "Segunda conversa"),
    ]

    set_cli_inputs(monkeypatch, ["/conversas", "/sair"])

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert "Conversas:" in output
    assert "Primeira conversa" in output
    assert "Segunda conversa" in output
    assert "conversation-1" in output
    assert "conversation-2" in output


@pytest.mark.asyncio
async def test_cli_displays_empty_conversation_list(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    set_cli_inputs(monkeypatch, ["/conversas", "/sair"])

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert "Nenhuma conversa encontrada." in output


@pytest.mark.asyncio
async def test_cli_opens_existing_conversation(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service.histories["conversation-2"] = [
        create_fake_message("user", "Olá!"),
        create_fake_message("assistant", "Olá, como posso ajudar?"),
    ]

    set_cli_inputs(
        monkeypatch,
        ["/abrir conversation-2", "Nova mensagem", "/sair"],
    )

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert "Conversa aberta." in output
    assert "[user] Olá!" in output
    assert "[assistant] Olá, como posso ajudar?" in output
    assert service.sent_messages == [("conversation-2", "Nova mensagem")]


@pytest.mark.asyncio
async def test_cli_displays_current_conversation_history(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service.histories["conversation-1"] = [
        create_fake_message("user", "Qual é o seu nome?"),
        create_fake_message("assistant", "Sou Guillotine."),
    ]

    set_cli_inputs(monkeypatch, ["/historico", "/sair"])

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert "Histórico:" in output
    assert "[user] Qual é o seu nome?" in output
    assert "[assistant] Sou Guillotine." in output


@pytest.mark.asyncio
async def test_cli_displays_empty_history(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    set_cli_inputs(monkeypatch, ["/historico", "/sair"])

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert "Esta conversa ainda não possui mensagens." in output


@pytest.mark.asyncio
async def test_cli_handles_model_error_and_continues(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service.send_message_error = ModelTimeoutError(
        "test-model",
        "timeout",
    )

    set_cli_inputs(
        monkeypatch,
        ["Primeira mensagem", "Segunda mensagem", "/sair"],
    )

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert "O modelo demorou demais para responder." in output
    assert "Resposta simulada." in output
    assert len(service.sent_messages) == 2


@pytest.mark.asyncio
async def test_cli_handles_validation_error_and_continues(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service.send_message_error = ValueError("Erro de validação.")

    set_cli_inputs(
        monkeypatch,
        ["Primeira mensagem", "Segunda mensagem", "/sair"],
    )

    await run_cli(cast(ConversationService, service))

    output = capsys.readouterr().out

    assert "Erro de validação." in output
    assert "Resposta simulada." in output
    assert len(service.sent_messages) == 2


@pytest.mark.asyncio
async def test_cli_propagates_unexpected_errors(
    service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service.send_message_error = RuntimeError("Erro inesperado.")

    set_cli_inputs(
        monkeypatch,
        ["Primeira mensagem", "/sair"],
    )

    with pytest.raises(RuntimeError, match="Erro inesperado."):
        await run_cli(cast(ConversationService, service))

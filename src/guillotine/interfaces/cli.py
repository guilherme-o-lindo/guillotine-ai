from guillotine.core.datetime import to_local_time
from guillotine.services.conversations import ConversationService


async def run_cli(service: ConversationService) -> None:
    conversation_id = await service.create("Nova conversa")

    print("\nGuillotine iniciado.")
    print("Digite /ajuda para consultar os comandos.\n")

    while True:
        user_input = input("Você: ").strip()

        if not user_input:
            continue

        if user_input == "/sair":
            print("\nGuillotine encerrado.")
            break

        if user_input == "/ajuda":
            print(
                "\nComandos disponíveis:\n"
                "  /nova       - iniciar nova conversa\n"
                "  /conversas  - listar conversas\n"
                "  /abrir ID   - abrir conversa existente\n"
                "  /historico  - visualizar histórico atual\n"
                "  /excluir    - excluir conversa atual\n"
                "  /ajuda      - mostrar comandos\n"
                "  /sair       - encerrar Guillotine\n"
            )
            continue

        if user_input == "/nova":
            conversation_id = await service.create("Nova conversa")
            print("\nNova conversa iniciada.\n")
            continue

        if user_input == "/conversas":
            conversations = await service.list()

            if not conversations:
                print("\nNenhuma conversa encontrada.\n")
                continue

            print("\nConversas:")

            for conversation in conversations:
                print(
                    f"- {conversation['title']} "
                    f"| ID: {conversation['id']} "
                    f"| Atualizada: {to_local_time(conversation['updated_at'])}"
                )

            print()
            continue

        if user_input.startswith("/abrir "):
            target_id = user_input.removeprefix("/abrir ").strip()

            try:
                history = await service.get_history(target_id)
                conversation_id = target_id

                print("\nConversa aberta.")

                if history:
                    print("\nHistórico:")

                    for message in history:
                        print(f"[{message['role']}] {message['content']}")

                print()

            except ValueError as error:
                print(f"\nErro: {error}\n")

            continue

        if user_input == "/historico":
            try:
                history = await service.get_history(conversation_id)

                if not history:
                    print("\nEsta conversa ainda não possui mensagens.\n")
                    continue

                print("\nHistórico:")

                for message in history:
                    print(f"[{message['role']}] {message['content']}")

                print()

            except ValueError as error:
                print(f"\nErro: {error}\n")

            continue

        if user_input == "/excluir":
            try:
                await service.delete(conversation_id)

                conversation_id = await service.create("Nova conversa")

                print("\nConversa excluída.")
                print("Uma nova conversa foi iniciada.\n")

            except ValueError as error:
                print(f"\nErro: {error}\n")

            continue

        try:
            response = await service.send_message(
                conversation_id,
                user_input,
            )

            print(f"\nGuillotine: {response}\n")

        except ValueError as error:
            print(f"\nErro: {error}\n")

import asyncio
import os
import signal
import subprocess
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

import httpx2

from guillotine.core.config import ROOT_DIR, settings


class RouterError(RuntimeError):
    """Erro durante o gerenciamento do 9Router."""


async def _is_available(client: httpx2.AsyncClient) -> bool:
    try:
        await client.get(settings.BASE_URL)
    except httpx2.HTTPError:
        return False

    # Qualquer resposta HTTP confirma que o servidor está ativo.
    # Isso inclui 401 Unauthorized e 403 Forbidden.
    return True


async def _start_router() -> asyncio.subprocess.Process:
    try:
        if sys.platform == "win32":
            return await asyncio.create_subprocess_exec(
                "cmd.exe",
                "/d",
                "/s",
                "/c",
                "pnpm exec 9router --tray --no-browser",
                cwd=ROOT_DIR,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )

        return await asyncio.create_subprocess_exec(
            "pnpm",
            "exec",
            "9router",
            "--tray",
            "--no-browser",
            cwd=ROOT_DIR,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            start_new_session=True,
        )

    except OSError as exc:
        raise RouterError(
            "Não foi possível iniciar o 9Router. "
            "Verifique se o pnpm está instalado e disponível no PATH."
        ) from exc


async def _stop_router(
    process: asyncio.subprocess.Process,
) -> None:
    if process.returncode is not None:
        return

    if sys.platform == "win32":
        try:
            taskkill = await asyncio.create_subprocess_exec(
                "taskkill",
                "/PID",
                str(process.pid),
                "/T",
                "/F",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await taskkill.wait()
        except OSError:
            process.terminate()
    else:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)

        try:
            await asyncio.wait_for(process.wait(), timeout=10)
        except TimeoutError:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)

    await process.wait()


@asynccontextmanager
async def router_lifecycle() -> AsyncGenerator[None, None]:
    process: asyncio.subprocess.Process | None = None

    async with httpx2.AsyncClient(timeout=2.0) as client:
        if not await _is_available(client):
            process = await _start_router()

            try:
                for _ in range(60):
                    if process.returncode is not None:
                        raise RouterError(
                            "O processo do 9Router foi encerrado "
                            "antes de ficar disponível."
                        )

                    if await _is_available(client):
                        break

                    await asyncio.sleep(1)
                else:
                    raise RouterError(
                        "O 9Router não ficou disponível dentro de 60 segundos."
                    )

                yield

            finally:
                await _stop_router(process)

        else:
            # Uma instância externa já está em execução.
            # Não assumimos responsabilidade pelo seu encerramento.
            yield

import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from guillotine.models import router


@pytest.fixture
def process() -> SimpleNamespace:
    return SimpleNamespace(
        pid=12345,
        returncode=None,
        wait=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_is_available_returns_true_for_http_response() -> None:
    client = MagicMock()
    client.get = AsyncMock(
        return_value=MagicMock(status_code=401),
    )

    result = await router._is_available(client)  # pyright: ignore[reportPrivateUsage]

    assert result is True
    client.get.assert_awaited_once_with(router.settings.BASE_URL)


@pytest.mark.asyncio
async def test_is_available_returns_false_on_http_error() -> None:
    client = MagicMock()
    client.get = AsyncMock(
        side_effect=router.httpx2.HTTPError("Connection failed"),
    )

    result = await router._is_available(client)  # pyright: ignore[reportPrivateUsage]

    assert result is False


@pytest.mark.asyncio
async def test_start_router_uses_tray_mode(
    monkeypatch: pytest.MonkeyPatch,
    process: SimpleNamespace,
) -> None:
    create_process = AsyncMock(return_value=process)

    monkeypatch.setattr(
        router.asyncio,
        "create_subprocess_exec",
        create_process,
    )

    result = await router._start_router()  # pyright: ignore[reportPrivateUsage]

    assert result is process

    args, kwargs = create_process.call_args

    if sys.platform == "win32":
        assert args == (
            "cmd.exe",
            "/d",
            "/s",
            "/c",
            "pnpm exec 9router --tray --no-browser",
        )
    else:
        assert args == (
            "pnpm",
            "exec",
            "9router",
            "--tray",
            "--no-browser",
        )
        assert kwargs["start_new_session"] is True

    assert kwargs["cwd"] == router.ROOT_DIR
    assert kwargs["stdin"] == router.asyncio.subprocess.DEVNULL
    assert kwargs["stdout"] == router.asyncio.subprocess.DEVNULL
    assert kwargs["stderr"] == router.asyncio.subprocess.DEVNULL


@pytest.mark.asyncio
async def test_start_router_raises_router_error_on_os_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_process = AsyncMock(
        side_effect=OSError("pnpm not found"),
    )

    monkeypatch.setattr(
        router.asyncio,
        "create_subprocess_exec",
        create_process,
    )

    with pytest.raises(router.RouterError):
        await router._start_router()  # pyright: ignore[reportPrivateUsage]


@pytest.mark.asyncio
async def test_existing_router_is_reused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    is_available = AsyncMock(return_value=True)
    start_router = AsyncMock()
    stop_router = AsyncMock()

    monkeypatch.setattr(router, "_is_available", is_available)
    monkeypatch.setattr(router, "_start_router", start_router)
    monkeypatch.setattr(router, "_stop_router", stop_router)

    async with router.router_lifecycle():
        pass

    start_router.assert_not_awaited()
    stop_router.assert_not_awaited()


@pytest.mark.asyncio
async def test_router_is_started_and_stopped_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    process: SimpleNamespace,
) -> None:
    is_available = AsyncMock(side_effect=[False, True])
    start_router = AsyncMock(return_value=process)
    stop_router = AsyncMock()

    monkeypatch.setattr(router, "_is_available", is_available)
    monkeypatch.setattr(router, "_start_router", start_router)
    monkeypatch.setattr(router, "_stop_router", stop_router)

    async with router.router_lifecycle():
        start_router.assert_awaited_once()

    stop_router.assert_awaited_once_with(process)


@pytest.mark.asyncio
async def test_router_startup_timeout_stops_process(
    monkeypatch: pytest.MonkeyPatch,
    process: SimpleNamespace,
) -> None:
    is_available = AsyncMock(return_value=False)
    start_router = AsyncMock(return_value=process)
    stop_router = AsyncMock()
    sleep = AsyncMock()

    monkeypatch.setattr(router, "_is_available", is_available)
    monkeypatch.setattr(router, "_start_router", start_router)
    monkeypatch.setattr(router, "_stop_router", stop_router)
    monkeypatch.setattr(router.asyncio, "sleep", sleep)

    with pytest.raises(router.RouterError, match="60 segundos"):
        async with router.router_lifecycle():
            pytest.fail("O contexto não deveria ser iniciado.")

    assert is_available.await_count == 61
    assert sleep.await_count == 60
    stop_router.assert_awaited_once_with(process)


@pytest.mark.asyncio
async def test_router_process_exit_before_startup_raises_error(
    monkeypatch: pytest.MonkeyPatch,
    process: SimpleNamespace,
) -> None:
    process.returncode = 1

    is_available = AsyncMock(return_value=False)
    start_router = AsyncMock(return_value=process)
    stop_router = AsyncMock()

    monkeypatch.setattr(router, "_is_available", is_available)
    monkeypatch.setattr(router, "_start_router", start_router)
    monkeypatch.setattr(router, "_stop_router", stop_router)

    with pytest.raises(router.RouterError, match="encerrado"):
        async with router.router_lifecycle():
            pytest.fail("O contexto não deveria ser iniciado.")

    stop_router.assert_awaited_once_with(process)


@pytest.mark.asyncio
async def test_router_is_stopped_when_application_raises_error(
    monkeypatch: pytest.MonkeyPatch,
    process: SimpleNamespace,
) -> None:
    is_available = AsyncMock(side_effect=[False, True])
    start_router = AsyncMock(return_value=process)
    stop_router = AsyncMock()

    monkeypatch.setattr(router, "_is_available", is_available)
    monkeypatch.setattr(router, "_start_router", start_router)
    monkeypatch.setattr(router, "_stop_router", stop_router)

    with pytest.raises(RuntimeError, match="Application error"):
        async with router.router_lifecycle():
            raise RuntimeError("Application error")

    stop_router.assert_awaited_once_with(process)

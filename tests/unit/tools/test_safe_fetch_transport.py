"""Transport-level regressions for Safe Fetch (no real network requests)."""

from __future__ import annotations

import socket
import ssl

import pytest

from guillotine.tools.local import safe_fetch


class FakeResponse:
    def __init__(
        self,
        *,
        status: int = 200,
        headers: list[tuple[str, str]] | None = None,
        body: bytes = b"Hello",
    ) -> None:
        self.status = status
        self._headers = (
            headers if headers is not None else [("Content-Type", "text/plain")]
        )
        self._body = body
        self.read_limit: int | None = None

    def getheaders(self) -> list[tuple[str, str]]:
        return self._headers

    def read(self, amount: int) -> bytes:
        self.read_limit = amount
        return self._body[:amount]


class FakeConnection:
    instances: list[FakeConnection] = []
    responses: list[FakeResponse] = []
    failures: set[str] = set()

    def __init__(
        self, host: str, port: int, ip: str, *, tls: bool, timeout: float
    ) -> None:
        self.host = host
        self.port = port
        self.ip = ip
        self.tls = tls
        self.timeout = timeout
        self.headers: dict[str, str] = {}
        self.path = ""
        self.closed = False
        self.instances.append(self)

    def request(self, method: str, path: str, *, headers: dict[str, str]) -> None:
        assert method == "GET"
        self.path = path
        self.headers = headers
        if self.ip in self.failures:
            raise OSError("simulated connection failure")

    def getresponse(self) -> FakeResponse:
        return self.responses.pop(0)

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_transport(monkeypatch: pytest.MonkeyPatch) -> type[FakeConnection]:
    FakeConnection.instances = []
    FakeConnection.responses = []
    FakeConnection.failures = set()
    monkeypatch.setattr(safe_fetch, "_PinnedConnection", FakeConnection)

    def fake_resolve(_host: str, _port: int) -> tuple[str, ...]:
        return ("8.8.8.8", "1.1.1.1")

    monkeypatch.setattr(safe_fetch, "resolve_public_ips", fake_resolve)
    return FakeConnection


def test_https_request_uses_pinned_ip_and_original_host(
    fake_transport: type[FakeConnection],
) -> None:
    response = FakeResponse(body=b"article")
    fake_transport.responses.append(response)

    result = safe_fetch.fetch_public_page("https://news.example.org/article?q=1")

    assert result.url == "https://news.example.org/article?q=1"
    assert result.text == "article"
    assert result.status == 200
    connection = fake_transport.instances[0]
    assert (connection.host, connection.ip, connection.port) == (
        "news.example.org",
        "8.8.8.8",
        443,
    )
    assert connection.tls is True
    assert connection.path == "/article?q=1"
    assert connection.headers["Host"] == "news.example.org"
    assert connection.headers["Accept-Encoding"] == "identity"
    assert connection.closed
    assert response.read_limit == 512_001


def test_fallback_only_uses_prevalidated_ips(
    fake_transport: type[FakeConnection],
) -> None:
    fake_transport.failures.add("8.8.8.8")
    fake_transport.responses.append(FakeResponse(body=b"fallback"))

    assert safe_fetch.fetch_public_page("http://news.example.org/").text == "fallback"
    assert [item.ip for item in fake_transport.instances] == ["8.8.8.8", "1.1.1.1"]
    assert all(item.closed for item in fake_transport.instances)


@pytest.mark.parametrize(
    ("headers", "body", "message"),
    [
        ([("Content-Type", "application/json")], b"{}", "content type"),
        (
            [("Content-Type", "text/plain"), ("Content-Encoding", "gzip")],
            b"compressed",
            "Compressed",
        ),
        (
            [("Content-Type", "text/plain"), ("Content-Length", "99")],
            b"short",
            "maximum size",
        ),
        ([("Content-Type", "text/plain")], b"oversized", "maximum size"),
    ],
)
def test_rejects_unsafe_responses_and_closes_connection(
    fake_transport: type[FakeConnection],
    headers: list[tuple[str, str]],
    body: bytes,
    message: str,
) -> None:
    fake_transport.responses.append(FakeResponse(headers=headers, body=body))
    with pytest.raises(safe_fetch.UnsafeDestination, match=message):
        safe_fetch.fetch_public_page("https://news.example.org/", max_bytes=5)
    assert fake_transport.instances[0].closed


def test_all_connection_attempts_fail_closed(
    fake_transport: type[FakeConnection],
) -> None:
    fake_transport.failures.update({"8.8.8.8", "1.1.1.1"})
    with pytest.raises(OSError, match="Could not connect"):
        safe_fetch.fetch_public_page("https://news.example.org/")
    assert len(fake_transport.instances) == 2
    assert all(connection.closed for connection in fake_transport.instances)


def test_redirect_is_rechecked_before_second_connection(
    fake_transport: type[FakeConnection],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_transport.responses.append(
        FakeResponse(
            status=302, headers=[("Location", "https://other.example.org/new")]
        )
    )
    fake_transport.responses.append(FakeResponse(body=b"destination"))
    resolved: list[str] = []

    def fake_resolve(host: str, _port: int) -> tuple[str, ...]:
        resolved.append(host)
        return ("8.8.8.8",)

    monkeypatch.setattr(safe_fetch, "resolve_public_ips", fake_resolve)
    result = safe_fetch.fetch_public_page("https://news.example.org/old")
    assert result.url == "https://other.example.org/new"
    assert result.text == "destination"
    assert resolved == ["news.example.org", "other.example.org"]
    assert all(connection.closed for connection in fake_transport.instances)


def test_redirect_with_no_location_is_denied(
    fake_transport: type[FakeConnection],
) -> None:
    fake_transport.responses.append(FakeResponse(status=302, headers=[]))
    with pytest.raises(safe_fetch.UnsafeDestination, match="without Location"):
        safe_fetch.fetch_public_page("https://news.example.org/")


def test_http_errors_are_not_returned_as_content(
    fake_transport: type[FakeConnection],
) -> None:
    fake_transport.responses.append(FakeResponse(status=404))
    with pytest.raises(ValueError, match="HTTP status 404"):
        safe_fetch.fetch_public_page("https://news.example.org/missing")


@pytest.mark.parametrize(
    "kwargs",
    [{"timeout": 0.0}, {"max_bytes": 0}, {"max_chars": -1}, {"max_redirects": -1}],
)
def test_invalid_limits_fail_before_network(kwargs: dict[str, int | float]) -> None:
    arguments = {
        "timeout": 8.0,
        "max_bytes": 512_000,
        "max_chars": 20_000,
        "max_redirects": 3,
    }
    arguments.update(kwargs)
    with pytest.raises(ValueError, match="Invalid fetch limits"):
        safe_fetch.fetch_public_page(
            "https://news.example.org/",
            timeout=float(arguments["timeout"]),
            max_bytes=int(arguments["max_bytes"]),
            max_chars=int(arguments["max_chars"]),
            max_redirects=int(arguments["max_redirects"]),
        )


def test_dns_failure_is_denied(monkeypatch: pytest.MonkeyPatch) -> None:
    def failed_dns(_host: str, _port: int, *, type: int) -> list[object]:
        raise socket.gaierror("missing")

    monkeypatch.setattr(safe_fetch.socket, "getaddrinfo", failed_dns)
    with pytest.raises(safe_fetch.UnsafeDestination, match="DNS resolution failed"):
        safe_fetch.resolve_public_ips("news.example.org", 443)


def test_dns_no_answers_is_denied(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_getaddrinfo(*_args: object, **_kwargs: object) -> list[object]:
        return []

    monkeypatch.setattr(safe_fetch.socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(safe_fetch.UnsafeDestination, match="no addresses"):
        safe_fetch.resolve_public_ips("news.example.org", 443)


def test_dns_deduplicates_public_addresses(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_getaddrinfo(*_args: object, **_kwargs: object) -> list[tuple[object, ...]]:
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443)),
        ]

    monkeypatch.setattr(safe_fetch.socket, "getaddrinfo", fake_getaddrinfo)
    assert safe_fetch.resolve_public_ips("news.example.org", 443) == (
        "8.8.8.8",
        "1.1.1.1",
    )


def test_https_tls_uses_original_host_for_certificate_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSocket:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    class FakeSSLContext:
        def wrap_socket(self, sock: FakeSocket, *, server_hostname: str) -> FakeSocket:
            assert server_hostname == "news.example.org"
            return sock

    raw = FakeSocket()

    def fake_create_connection(*_args: object, **_kwargs: object) -> FakeSocket:
        return raw

    monkeypatch.setattr(safe_fetch.socket, "create_connection", fake_create_connection)

    def fake_ssl_context(_protocol: int) -> FakeSSLContext:
        return FakeSSLContext()

    monkeypatch.setattr(safe_fetch.truststore, "SSLContext", fake_ssl_context)
    connection = safe_fetch._PinnedConnection(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        "news.example.org", 443, "8.8.8.8", tls=True, timeout=4
    )
    connection.connect()
    assert connection.sock is raw


def test_tls_failure_closes_underlying_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSocket:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    class BrokenSSLContext:
        def wrap_socket(self, _sock: FakeSocket, *, server_hostname: str) -> FakeSocket:
            raise ssl.SSLError("bad certificate")

    raw = FakeSocket()

    def fake_create_connection(*_args: object, **_kwargs: object) -> FakeSocket:
        return raw

    monkeypatch.setattr(safe_fetch.socket, "create_connection", fake_create_connection)

    def broken_ssl_context(_protocol: int) -> BrokenSSLContext:
        return BrokenSSLContext()

    monkeypatch.setattr(safe_fetch.truststore, "SSLContext", broken_ssl_context)
    connection = safe_fetch._PinnedConnection(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        "news.example.org", 443, "8.8.8.8", tls=True, timeout=4
    )
    with pytest.raises(ssl.SSLError):
        connection.connect()
    assert raw.closed

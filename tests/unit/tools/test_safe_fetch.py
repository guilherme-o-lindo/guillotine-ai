"""Safety regression tests for the pinned public-web fetcher."""

from __future__ import annotations

import socket

import pytest

from guillotine.tools.local import safe_fetch


@pytest.mark.parametrize(
    "url",
    [
        "ref://abc",
        "file:///etc/passwd",
        "http://localhost/",
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://192.168.1.1/",
        "http://169.254.169.254/",
        "https://example.com@localhost/",
        "https://localhost.example/",
        "http://web.test/",
        "http://web.internal/",
        "http://web.example:8080/",
        "https://web.example/#frag",
        "https://web.example/\\evil",
        "https://web.example/\n",
        "https://user:pass@web.example/",
    ],
)
def test_rejects_unsafe_urls(url: str) -> None:
    with pytest.raises(safe_fetch.UnsafeDestination):
        safe_fetch.parse_public_url(url)


def test_resolve_rejects_mixed_public_and_private_dns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_getaddrinfo(
        host: str, port: int, *, type: int
    ) -> list[tuple[int, int, int, str, tuple[str, int]]]:
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", port)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port)),
        ]

    monkeypatch.setattr(safe_fetch.socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(safe_fetch.UnsafeDestination, match="nonpublic"):
        safe_fetch.resolve_public_ips("public.example.org", 443)


def test_follows_redirects_only_after_revalidating_destination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempted: list[str] = []

    def fake_fetch(
        url: str, *, timeout: float, max_bytes: int
    ) -> tuple[int, dict[str, str], bytes]:
        attempted.append(url)
        return 302, {"location": "http://127.0.0.1/admin"}, b""

    monkeypatch.setattr(safe_fetch, "_fetch_once", fake_fetch)
    with pytest.raises(safe_fetch.UnsafeDestination):
        safe_fetch.fetch_public_page("https://public.example.org/start")
    assert attempted == ["https://public.example.org/start"]


def test_extracts_text_and_limits_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch(
        url: str, *, timeout: float, max_bytes: int
    ) -> tuple[int, dict[str, str], bytes]:
        return (
            200,
            {"content-type": "text/html"},
            b"<h1>Title</h1><script>secret</script><p>Body text</p>",
        )

    monkeypatch.setattr(safe_fetch, "_fetch_once", fake_fetch)
    response = safe_fetch.fetch_public_page("https://public.example.org/", max_chars=10)
    assert response.text == "Title\nBody"[:10]
    assert "secret" not in response.text


def test_rejects_unbounded_redirect_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch(
        url: str, *, timeout: float, max_bytes: int
    ) -> tuple[int, dict[str, str], bytes]:
        return 302, {"location": "/again"}, b""

    monkeypatch.setattr(safe_fetch, "_fetch_once", fake_fetch)
    with pytest.raises(safe_fetch.UnsafeDestination, match="Too many"):
        safe_fetch.fetch_public_page("https://public.example.org/", max_redirects=2)


def test_extracts_structured_html_with_redirect_and_charset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested: list[str] = []

    def fake_fetch(
        url: str, *, timeout: float, max_bytes: int
    ) -> tuple[int, dict[str, str], bytes]:
        requested.append(url)
        if url.endswith("/start"):
            return 302, {"location": "/final"}, b""
        return (
            200,
            {"content-type": "text/html; charset=iso-8859-1"},
            (
                "<html><head><title>Pesquisa</title>"
                '<meta name="description" content="Resumo"></head>'
                "<body><nav>Menu</nav><main><h1>Artigo</h1>"
                '<p>Informação útil</p><a href="/docs">Documentação</a>'
                "</main><script>oculto</script></body></html>"
            ).encode("latin-1"),
        )

    monkeypatch.setattr(safe_fetch, "_fetch_once", fake_fetch)
    result = safe_fetch.fetch_public_page("https://public.example.org/start")
    assert requested == [
        "https://public.example.org/start",
        "https://public.example.org/final",
    ]
    assert result.url == "https://public.example.org/final"
    assert result.content_type == "text/html"
    assert result.page is not None
    assert result.page.title == "Pesquisa"
    assert result.page.description == "Resumo"
    assert "Informação útil" in result.text
    assert "Menu" not in result.text
    assert "oculto" not in result.text
    assert result.page.links[0].url == "https://public.example.org/docs"


def test_plain_text_does_not_create_structured_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_fetch(
        url: str, *, timeout: float, max_bytes: int
    ) -> tuple[int, dict[str, str], bytes]:
        return 200, {"content-type": "text/plain"}, b"plain text"

    monkeypatch.setattr(safe_fetch, "_fetch_once", fake_fetch)
    result = safe_fetch.fetch_public_page("https://public.example.org/plain")
    assert result.text == "plain text"
    assert result.page is None


def test_rejects_unsupported_html_charset_after_guarded_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from guillotine.tools.local.html_response import UnsupportedHTMLResponse

    def fake_fetch(
        url: str, *, timeout: float, max_bytes: int
    ) -> tuple[int, dict[str, str], bytes]:
        return 200, {"content-type": "text/html; charset=utf-7"}, b"html"

    monkeypatch.setattr(safe_fetch, "_fetch_once", fake_fetch)
    with pytest.raises(UnsupportedHTMLResponse, match="Unsupported HTML charset"):
        safe_fetch.fetch_public_page("https://public.example.org/html")


def test_https_uses_os_trust_store_and_preserves_pinned_ip_and_sni(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import Mock

    raw_socket = Mock()
    verified_socket = Mock()
    create_connection = Mock(return_value=raw_socket)
    context = Mock()
    context.wrap_socket.return_value = verified_socket
    create_context = Mock(return_value=context)
    monkeypatch.setattr(safe_fetch.socket, "create_connection", create_connection)
    monkeypatch.setattr(safe_fetch.truststore, "SSLContext", create_context)

    connection = safe_fetch._PinnedConnection(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        "example.com", 443, "93.184.215.14", tls=True, timeout=3.0
    )
    connection.connect()

    create_connection.assert_called_once_with(("93.184.215.14", 443), timeout=3.0)
    create_context.assert_called_once_with(safe_fetch.ssl.PROTOCOL_TLS_CLIENT)
    context.wrap_socket.assert_called_once_with(
        raw_socket, server_hostname="example.com"
    )
    assert connection.sock is verified_socket


def test_https_closes_raw_socket_if_tls_validation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import Mock

    raw_socket = Mock()
    monkeypatch.setattr(
        safe_fetch.socket, "create_connection", Mock(return_value=raw_socket)
    )
    context = Mock()
    context.wrap_socket.side_effect = safe_fetch.ssl.SSLError("untrusted chain")
    monkeypatch.setattr(safe_fetch.truststore, "SSLContext", Mock(return_value=context))

    connection = safe_fetch._PinnedConnection(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        "example.com", 443, "93.184.215.14", tls=True, timeout=3.0
    )
    with pytest.raises(safe_fetch.ssl.SSLError, match="untrusted chain"):
        connection.connect()
    raw_socket.close.assert_called_once_with()

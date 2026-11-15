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

"""Conservative public-web fetcher with destination validation at connection time.

No proxy support, no ref:// resolution, no cookies, no automatic redirects.
This is NOT wired to the external DuckDuckGo MCP fetch_content tool.
"""

from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import truststore

from guillotine.tools.local.html_extract import ExtractedPage
from guillotine.tools.local.html_response import extract_fetched_html

_MAX_URL = 4096
_REDIRECTS = frozenset({301, 302, 303, 307, 308})
_ALLOWED_CONTENT_TYPES = frozenset({"text/html", "text/plain", "application/xhtml+xml"})
_BAD_SUFFIXES = (
    ".localhost",
    ".local",
    ".localdomain",
    ".internal",
    ".home.arpa",
    ".test",
    ".invalid",
    ".example",
    ".onion",
)


class UnsafeDestination(ValueError):
    """URL or resolved network address is not allowed."""


@dataclass(frozen=True, slots=True)
class FetchResult:
    url: str
    text: str
    content_type: str
    status: int
    page: ExtractedPage | None = None


def parse_public_url(url: str) -> tuple[str, str, int, str]:
    if (
        not url
        or len(url) > _MAX_URL
        or url != url.strip()
        or any(ord(c) < 33 or ord(c) > 126 for c in url)
        or "\\" in url
    ):
        raise UnsafeDestination("Invalid URL")
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise UnsafeDestination("Malformed URL") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or "@" in parsed.netloc
        or "%" in parsed.netloc
    ):
        raise UnsafeDestination("Only public HTTP(S) URLs are allowed")
    if port not in {None, 80 if parsed.scheme == "http" else 443}:
        raise UnsafeDestination("Nonstandard ports are blocked")
    hostname = host.lower()
    labels = hostname.split(".")
    if (
        len(hostname) > 253
        or len(labels) < 2
        or hostname.endswith(_BAD_SUFFIXES)
        or hostname in {"localhost", "metadata.google.internal"}
        or labels[-1].isdigit()
        or any(
            not label
            or len(label) > 63
            or label[0] == "-"
            or label[-1] == "-"
            or not all(ch.isascii() and (ch.isalnum() or ch == "-") for ch in label)
            for label in labels
        )
    ):
        raise UnsafeDestination("Only public DNS hostnames are allowed")
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise UnsafeDestination("Literal IP addresses are blocked")
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    return (
        parsed.scheme,
        hostname,
        port or (443 if parsed.scheme == "https" else 80),
        path,
    )


def resolve_public_ips(host: str, port: int) -> tuple[str, ...]:
    """Resolve immediately before connecting; reject entire mixed DNS answers."""
    try:
        answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise UnsafeDestination("DNS resolution failed") from exc
    if not answers:
        raise UnsafeDestination("DNS returned no addresses")
    ips: list[str] = []
    for family, _, _, _, sockaddr in answers:
        if family not in {socket.AF_INET, socket.AF_INET6}:
            raise UnsafeDestination("Unsupported DNS address family")
        ip = ipaddress.ip_address(sockaddr[0])
        if not ip.is_global:
            raise UnsafeDestination("DNS returned a nonpublic address")
        if str(ip) not in ips:
            ips.append(str(ip))
    return tuple(ips)


class _PinnedConnection(http.client.HTTPConnection):
    """Make the TCP connection to the vetted IP, never resolve the hostname again."""

    def __init__(
        self, host: str, port: int, ip: str, *, tls: bool, timeout: float
    ) -> None:
        super().__init__(host, port=port, timeout=timeout)
        self._ip = ip
        self._tls = tls

    def connect(self) -> None:
        raw = socket.create_connection((self._ip, self.port), timeout=self.timeout)
        if not self._tls:
            self.sock = raw
            return
        try:
            # Cert verification and SNI refer to the original hostname.
            # Use OS trust roots (Windows certificate store) while preserving
            # certificate validation and SNI for the original hostname.
            context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            self.sock = context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


def _fetch_once(
    url: str, *, timeout: float, max_bytes: int
) -> tuple[int, dict[str, str], bytes]:
    scheme, host, port, path = parse_public_url(url)
    ips = resolve_public_ips(host, port)
    # On connection failure, retry only previously validated public IP addresses.
    last_error: OSError | None = None
    for ip in ips:
        connection = _PinnedConnection(
            host, port, ip, tls=scheme == "https", timeout=timeout
        )
        try:
            connection.request(
                "GET",
                path,
                headers={
                    "Host": host,
                    "Accept": "text/html, text/plain, application/xhtml+xml",
                    "Accept-Encoding": "identity",
                    "User-Agent": "GuillotineSafeFetch/0.3",
                    "Connection": "close",
                },
            )
            response = connection.getresponse()
            headers = {key.lower(): value for key, value in response.getheaders()}
            content_type = (
                headers.get("content-type", "").split(";", 1)[0].lower().strip()
            )
            if (
                response.status not in _REDIRECTS
                and content_type not in _ALLOWED_CONTENT_TYPES
            ):
                raise UnsafeDestination("Unsupported response content type")
            if headers.get("content-encoding", "identity").lower() != "identity":
                raise UnsafeDestination("Compressed responses are not accepted")
            length = headers.get("content-length")
            if length is not None and int(length) > max_bytes:
                raise UnsafeDestination("Response exceeds maximum size")
            data = response.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise UnsafeDestination("Response exceeds maximum size")
            return response.status, headers, data
        except OSError as exc:
            last_error = exc
        finally:
            connection.close()
    raise OSError("Could not connect to a validated public IP") from last_error


def fetch_public_page(
    url: str,
    *,
    timeout: float = 8.0,
    max_bytes: int = 512_000,
    max_redirects: int = 3,
    max_chars: int = 20_000,
) -> FetchResult:
    """Fetch plain text from a public page, with URL/DNS validation per redirect.

    This function performs blocking I/O. In an async tool, use asyncio.to_thread.
    Never pass ref:// tokens here; resolve those separately to full URLs first.
    """
    if timeout <= 0 or max_bytes <= 0 or max_chars <= 0 or max_redirects < 0:
        raise ValueError("Invalid fetch limits")
    current = url
    for _ in range(max_redirects + 1):
        parse_public_url(current)
        status, headers, body = _fetch_once(
            current, timeout=timeout, max_bytes=max_bytes
        )
        if status in _REDIRECTS:
            location = headers.get("location")
            if not location:
                raise UnsafeDestination("Redirect without Location")
            current = urljoin(current, location)
            continue
        if not 200 <= status < 300:
            raise ValueError(f"HTTP status {status}")
        content_type = (
            headers.get("content-type", "text/plain").split(";", 1)[0].lower().strip()
        )
        if content_type not in _ALLOWED_CONTENT_TYPES:
            raise UnsafeDestination("Unsupported response content type")
        if content_type == "text/plain":
            # Preserve the existing plain-text response contract.
            text = body.decode("utf-8", errors="replace")[:max_chars]
            return FetchResult(
                url=current, text=text, content_type=content_type, status=status
            )

        # Parse only bytes already obtained through the SSRF-guarded transport.
        # The full Content-Type retains its charset parameter for decoding.
        page = extract_fetched_html(
            body,
            final_url=current,
            content_type=headers.get("content-type", content_type),
            max_body_bytes=max_bytes,
            max_content_chars=max_chars,
        )
        return FetchResult(
            url=current,
            text=page.content,
            content_type=content_type,
            status=status,
            page=page,
        )
    raise UnsafeDestination("Too many HTTP redirects")

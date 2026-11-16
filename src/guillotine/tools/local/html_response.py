"""Convert an *already authorized and fetched* HTML response to structured data.

This module performs no I/O, DNS resolution or permission decisions.
"""

from __future__ import annotations

import codecs
from email.message import Message

from guillotine.tools.local.html_extract import ExtractedPage, extract_html


class UnsupportedHTMLResponse(ValueError):
    """The fetched response is not acceptable as an HTML document."""


def extract_fetched_html(
    body: bytes,
    *,
    final_url: str,
    content_type: str,
    max_body_bytes: int = 512_000,
    max_content_chars: int = 20_000,
    max_links: int = 50,
) -> ExtractedPage:
    """Parse bounded HTML bytes returned by an existing trusted fetch transport.

    The caller MUST have completed URL validation, redirect checks, DNS/IP
    pinning and the ToolExecutor permission flow before calling this function.
    """
    if max_body_bytes < 1 or max_content_chars < 1 or max_links < 0:
        raise ValueError("Invalid extraction limit")
    if len(body) > max_body_bytes:
        raise UnsupportedHTMLResponse("HTML response body exceeds limit")

    header = Message()
    header["content-type"] = content_type
    media_type = header.get_content_type().lower()
    if media_type not in {"text/html", "application/xhtml+xml"}:
        raise UnsupportedHTMLResponse("Response is not HTML")

    charset = header.get_param("charset", header="content-type")
    if not isinstance(charset, str) or not charset.strip():
        charset = "utf-8"
    try:
        codec = codecs.lookup(charset)
    except LookupError as exc:
        raise UnsupportedHTMLResponse("Unknown HTML charset") from exc
    # Avoid ambiguous or potentially unsafe encodings. UTF-16/32 may be
    # supported later with explicit byte-order handling.
    if codec.name not in {"utf-8", "iso8859-1", "cp1252", "ascii"}:
        raise UnsupportedHTMLResponse("Unsupported HTML charset")
    html = body.decode(codec.name, errors="replace")
    return extract_html(
        html,
        final_url=final_url,
        max_html_chars=max_body_bytes,
        max_content_chars=max_content_chars,
        max_links=max_links,
    )

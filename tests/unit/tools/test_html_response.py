"""No-network checks for the HTML response conversion boundary."""

from __future__ import annotations

import pytest

from guillotine.tools.local.html_response import (
    UnsupportedHTMLResponse,
    extract_fetched_html,
)

URL = "https://example.org/research"


def test_extracts_already_fetched_html_bytes() -> None:
    result = extract_fetched_html(
        b"<title>Research</title><main><p>Useful text</p></main>",
        final_url=URL,
        content_type="text/html; charset=utf-8",
    )
    assert result.url == URL
    assert result.title == "Research"
    assert "Useful text" in result.content


def test_accepts_latin1_header() -> None:
    result = extract_fetched_html(
        "<main>Informação</main>".encode("latin-1"),
        final_url=URL,
        content_type="text/html; charset=iso-8859-1",
    )
    assert "Informação" in result.content


@pytest.mark.parametrize(
    "media_type", ["application/json", "text/plain", "image/svg+xml"]
)
def test_rejects_non_html(media_type: str) -> None:
    with pytest.raises(UnsupportedHTMLResponse, match="not HTML"):
        extract_fetched_html(
            b"<main>Text</main>", final_url=URL, content_type=media_type
        )


def test_rejects_unknown_charset() -> None:
    with pytest.raises(UnsupportedHTMLResponse, match="Unknown HTML charset"):
        extract_fetched_html(
            b"<main>Text</main>", final_url=URL, content_type="text/html; charset=nope"
        )


def test_rejects_unsupported_charset() -> None:
    with pytest.raises(UnsupportedHTMLResponse, match="Unsupported HTML charset"):
        extract_fetched_html(
            b"<main>Text</main>", final_url=URL, content_type="text/html; charset=utf-7"
        )


def test_rejects_oversize_before_decode() -> None:
    with pytest.raises(UnsupportedHTMLResponse, match="exceeds limit"):
        extract_fetched_html(
            b"x" * 101, final_url=URL, content_type="text/html", max_body_bytes=100
        )


def test_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError, match="Invalid extraction limit"):
        extract_fetched_html(
            b"<main></main>", final_url=URL, content_type="text/html", max_links=-1
        )

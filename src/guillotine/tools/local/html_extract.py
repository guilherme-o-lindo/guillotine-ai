"""Pure HTML-to-document extraction. No network I/O or permissions decisions.

Input HTML is untrusted; callers must obtain it through the authorized fetcher.
The ``url`` argument is the *final fetched URL*, not a canonical URL from HTML.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

_BLOCK = frozenset(
    {
        "address",
        "article",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "li",
        "main",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
)
_SUPPRESSED = frozenset(
    {
        "script",
        "style",
        "noscript",
        "svg",
        "template",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
    }
)
_VOID = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class PageLink:
    text: str
    url: str


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    url: str
    title: str | None
    description: str | None
    content: str
    links: tuple[PageLink, ...]


def _normal(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


def _link_url(base: str, href: str) -> str | None:
    if not href or any(ord(c) < 32 or ord(c) == 127 for c in href):
        return None
    try:
        url = urljoin(base, href)
        parts = urlsplit(url)
        if parts.scheme not in {"https", "http"} or not parts.hostname:
            return None
        if parts.username is not None or parts.password is not None:
            return None
        return url
    except ValueError:
        return None


class _PageParser(HTMLParser):
    def __init__(self, base_url: str, *, max_chars: int, max_links: int) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.max_chars = max_chars
        self.max_links = max_links
        self.title_chunks: list[str] = []
        self.description: str | None = None
        self.body_chunks: list[str] = []
        self.main_chunks: list[str] = []
        self.article_chunks: list[str] = []
        self.links: list[PageLink] = []
        self._tags: list[str] = []
        self._suppressed = 0
        self._main = 0
        self._article = 0
        self._title = 0
        self._anchor: tuple[str, list[str]] | None = None
        self._chars = 0
        self._seen_urls: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attributes = dict(attrs)
        if tag == "meta" and self.description is None:
            key = (attributes.get("name") or attributes.get("property") or "").lower()
            if key in {"description", "og:description"}:
                description = _normal(attributes.get("content") or "")
                if description:
                    self.description = description[:500]
        if tag not in _VOID:
            self._tags.append(tag)
        if tag in _SUPPRESSED:
            self._suppressed += 1
        if tag == "main":
            self._main += 1
        if tag == "article":
            self._article += 1
        if tag == "title":
            self._title += 1
        if self._suppressed:
            return
        if tag in _BLOCK:
            self._append("\n")
        if tag == "a" and self._anchor is None and len(self.links) < self.max_links:
            href = attributes.get("href")
            url = _link_url(self.base_url, href) if href is not None else None
            if url is not None and url not in self._seen_urls:
                self._anchor = (url, [])

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _VOID:
            return
        # Account for malformed markup without allowing a mismatched close tag
        # to decrement the suppression counters.
        if tag not in self._tags:
            return
        while self._tags:
            popped = self._tags.pop()
            if popped == "a" and self._anchor is not None:
                url, chunks = self._anchor
                label = _normal("".join(chunks))[:160]
                if label and len(self.links) < self.max_links:
                    self._seen_urls.add(url)
                    self.links.append(PageLink(text=label, url=url))
                self._anchor = None
            if popped in _SUPPRESSED:
                self._suppressed -= 1
            if popped == "main":
                self._main -= 1
            if popped == "article":
                self._article -= 1
            if popped == "title":
                self._title -= 1
            if popped in _BLOCK and not self._suppressed:
                self._append("\n")
            if popped == tag:
                break

    def handle_data(self, data: str) -> None:
        if self._title:
            self.title_chunks.append(data[:500])
        if self._suppressed:
            return
        self._append(data)
        if self._anchor is not None:
            self._anchor[1].append(data[:160])

    def _append(self, value: str) -> None:
        if self._chars >= self.max_chars * 4:
            return
        value = value[: self.max_chars * 4 - self._chars]
        self._chars += len(value)
        self.body_chunks.append(value)
        if self._main:
            self.main_chunks.append(value)
        if self._article:
            self.article_chunks.append(value)

    def extract(self) -> ExtractedPage:
        content = "".join(self.main_chunks or self.article_chunks or self.body_chunks)
        lines = [_normal(line) for line in content.splitlines()]
        cleaned = "\n".join(line for line in lines if line)[: self.max_chars]
        title = _normal("".join(self.title_chunks))[:300] or None
        return ExtractedPage(
            url=self.base_url,
            title=title,
            description=self.description,
            content=cleaned,
            links=tuple(self.links),
        )


def extract_html(
    html: str,
    *,
    final_url: str,
    max_html_chars: int = 512_000,
    max_content_chars: int = 20_000,
    max_links: int = 50,
) -> ExtractedPage:
    """Extract bounded, structured page data from already-fetched HTML.

    Never fetch URLs found in links. Parsing does not imply source trust.
    """
    if max_html_chars < 1 or max_content_chars < 1 or max_links < 0:
        raise ValueError("Extraction limits must be positive (links may be zero)")
    if len(html) > max_html_chars:
        raise ValueError("HTML exceeds extraction limit")
    parts = urlsplit(final_url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("final_url must be an absolute HTTP(S) URL")
    parser = _PageParser(final_url, max_chars=max_content_chars, max_links=max_links)
    parser.feed(html)
    parser.close()
    return parser.extract()

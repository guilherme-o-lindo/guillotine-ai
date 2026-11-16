"""Bounded, read-only filesystem operations under an explicitly configured root.

These are primitives, not agent tools: registration and permissions must remain
in ToolRegistry/ToolExecutor. Path checks are not an OS sandbox against races.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_SKIP_DIRS = frozenset(
    {".git", ".venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache"}
)


@dataclass(frozen=True, slots=True)
class FileReaderLimits:
    max_entries: int = 100
    max_read_bytes: int = 128_000
    max_chars: int = 20_000
    max_search_files: int = 200
    max_search_bytes: int = 64_000
    max_matches: int = 40
    max_depth: int = 6


class LocalFileReader:
    """Best-effort filesystem guard for a trusted, local read-only agent tool."""

    def __init__(self, root: Path, limits: FileReaderLimits | None = None) -> None:
        if not root.is_absolute() or not root.is_dir():
            raise ValueError("Authorized root must be an existing absolute directory")
        self.root = root.resolve(strict=True)
        self.limits = limits or FileReaderLimits()
        if any(value <= 0 for value in vars_from_limits(self.limits)):
            raise ValueError("All file-reading limits must be positive")

    def _resolve(self, relative_path: str) -> Path:
        if not relative_path or "\x00" in relative_path:
            raise ValueError("Invalid relative path")
        # Treat Windows-style input as unsafe on POSIX as well.
        if (
            "\\" in relative_path
            or ":" in relative_path
            or relative_path.startswith("/")
        ):
            raise PermissionError(
                "Only relative paths with '/' separators are supported"
            )
        candidate = Path(relative_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise PermissionError("Path must stay within the authorized root")
        # Reject redirection at every component, including Windows junctions.
        # This is a best-effort check; concurrent replacements require OS-level
        # handle-based confinement and are not prevented by path inspection.
        current = self.root
        for part in candidate.parts:
            current = current / part
            if _is_redirect(current):
                raise PermissionError("Path crosses a symbolic link or junction")
        resolved = current.resolve(strict=True)
        if not resolved.is_relative_to(self.root):
            raise PermissionError("Path escapes the authorized root")
        return resolved

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a model path within this authorized root before permission checks."""
        return self._resolve(relative_path)

    def list_directory(self, relative_path: str = ".") -> dict[str, object]:
        directory = self._resolve(relative_path)
        if not directory.is_dir():
            raise ValueError("Path is not a directory")
        entries: list[dict[str, object]] = []
        for child in sorted(directory.iterdir(), key=lambda p: p.name.casefold()):
            if len(entries) >= self.limits.max_entries:
                break
            # Do not enumerate symlinks, even if their targets happen to be inside root.
            if _is_redirect(child):
                continue
            entries.append(
                {"name": child.name, "type": "directory" if child.is_dir() else "file"}
            )
        return {
            "path": directory.relative_to(self.root).as_posix(),
            "entries": entries,
            "truncated": len(entries) >= self.limits.max_entries,
        }

    def read_file(self, relative_path: str) -> dict[str, object]:
        target = self._resolve(relative_path)
        if not target.is_file():
            raise ValueError("Path is not a regular file")
        with target.open("rb") as handle:
            data = handle.read(self.limits.max_read_bytes + 1)
        if len(data) > self.limits.max_read_bytes:
            raise ValueError("File exceeds reading limit")
        if b"\x00" in data:
            raise ValueError("Binary files are not supported")
        try:
            text = data.decode("utf-8-sig")
        except UnicodeError as exc:
            raise ValueError("File is not valid UTF-8") from exc
        return {
            "path": target.relative_to(self.root).as_posix(),
            "content": text[: self.limits.max_chars],
            "truncated": len(text) > self.limits.max_chars,
        }

    def search_files(self, query: str, relative_path: str = ".") -> dict[str, object]:
        if not query or len(query) > 200 or "\x00" in query:
            raise ValueError("Search query must contain 1 to 200 characters")
        start = self._resolve(relative_path)
        if not start.is_dir():
            raise ValueError("Search path is not a directory")
        matches: list[dict[str, object]] = []
        scanned = 0
        truncated = False
        pending: list[tuple[Path, int]] = [(start, 0)]
        needle = query.casefold()
        while pending:
            directory, depth = pending.pop()
            children = sorted(directory.iterdir(), key=lambda p: p.name.casefold())
            for child in children:
                if _is_redirect(child):
                    continue
                resolved = child.resolve(strict=True)
                if not resolved.is_relative_to(self.root):
                    continue
                if child.is_dir():
                    if depth < self.limits.max_depth and child.name not in _SKIP_DIRS:
                        pending.append((child, depth + 1))
                    continue
                if not child.is_file():
                    continue
                if scanned >= self.limits.max_search_files:
                    truncated = True
                    break
                scanned += 1
                with child.open("rb") as handle:
                    data = handle.read(self.limits.max_search_bytes + 1)
                if len(data) > self.limits.max_search_bytes or b"\x00" in data:
                    continue
                try:
                    content = data.decode("utf-8-sig")
                except UnicodeError:
                    continue
                for line_number, line in enumerate(content.splitlines(), start=1):
                    if needle not in line.casefold():
                        continue
                    matches.append(
                        {
                            "path": resolved.relative_to(self.root).as_posix(),
                            "line": line_number,
                            "text": line[:300],
                        }
                    )
                    if len(matches) >= self.limits.max_matches:
                        truncated = True
                        break
                if truncated:
                    break
            if truncated:
                break
        return {
            "query": query,
            "matches": matches,
            "files_scanned": scanned,
            "truncated": truncated,
        }


def vars_from_limits(limits: FileReaderLimits) -> tuple[int, ...]:
    return (
        limits.max_entries,
        limits.max_read_bytes,
        limits.max_chars,
        limits.max_search_files,
        limits.max_search_bytes,
        limits.max_matches,
        limits.max_depth,
    )


def _is_redirect(path: Path) -> bool:
    """Detect links and Windows junctions before traversing a local path."""
    return path.is_symlink() or path.is_junction()

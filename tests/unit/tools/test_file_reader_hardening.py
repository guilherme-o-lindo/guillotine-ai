"""Additional local-file security regression tests for Guillotine v0.3.0."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

from guillotine.tools.local.file_reader import FileReaderLimits, LocalFileReader


def test_list_limit_and_no_redirects(tmp_path: Path) -> None:
    for index in range(5):
        (tmp_path / f"item-{index}.txt").write_text("x", encoding="utf-8")
    reader = LocalFileReader(tmp_path, FileReaderLimits(max_entries=2))
    result = reader.list_directory()
    entries = result["entries"]
    assert isinstance(entries, list)
    assert len(cast(list[object], result["entries"])) == 2
    assert result["truncated"] is True


def test_utf8_character_limit(tmp_path: Path) -> None:
    (tmp_path / "utf8.txt").write_text("áéíóú", encoding="utf-8")
    result = LocalFileReader(tmp_path, FileReaderLimits(max_chars=3)).read_file(
        "utf8.txt"
    )
    assert result["content"] == "áéí"
    assert result["truncated"] is True


def test_search_respects_file_limit(tmp_path: Path) -> None:
    for index in range(4):
        (tmp_path / f"{index}.txt").write_text("needle", encoding="utf-8")
    result = LocalFileReader(
        tmp_path, FileReaderLimits(max_search_files=1)
    ).search_files("needle")
    assert result["files_scanned"] == 1
    assert result["truncated"] is True


def test_search_skips_binary_and_oversized_files(tmp_path: Path) -> None:
    (tmp_path / "binary.dat").write_bytes(b"needle\x00data")
    (tmp_path / "large.txt").write_text("needle " * 30, encoding="utf-8")
    (tmp_path / "valid.txt").write_text("needle", encoding="utf-8")
    result = LocalFileReader(
        tmp_path, FileReaderLimits(max_search_bytes=32)
    ).search_files("needle")
    assert result["matches"] == [{"path": "valid.txt", "line": 1, "text": "needle"}]


def test_reject_windows_paths_and_traversal(tmp_path: Path) -> None:
    reader = LocalFileReader(tmp_path)
    for path in (
        "../outside.txt",
        "/etc/passwd",
        "C:/Windows/system.ini",
        "C:relative.txt",
        "\\\\server\\share\\data.txt",
        "folder\\file.txt",
    ):
        with pytest.raises(PermissionError):
            reader.read_file(path)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows junction only")
def test_real_windows_junction_is_blocked(tmp_path: Path) -> None:
    """Uses cmd mklink /J; no Developer Mode or symlink privilege needed normally."""
    root = tmp_path / "authorized"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("do-not-read", encoding="utf-8")
    junction = root / "redirect"
    creation = subprocess.run(
        ["cmd", "/d", "/c", "mklink", "/J", str(junction), str(outside)],
        capture_output=True,
        text=True,
        check=False,
    )
    if creation.returncode != 0 or not junction.is_junction():
        pytest.skip("Junction creation unavailable on this Windows host")
    try:
        reader = LocalFileReader(root)
        with pytest.raises(PermissionError, match="symbolic link or junction"):
            reader.read_file("redirect/secret.txt")
        assert reader.list_directory()["entries"] == []
        assert reader.search_files("do-not-read")["matches"] == []
    finally:
        # Remove the reparse point only; do not recursively delete its target.
        os.rmdir(junction)
        assert (outside / "secret.txt").read_text(encoding="utf-8") == "do-not-read"

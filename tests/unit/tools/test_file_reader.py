from pathlib import Path
from typing import cast

import pytest

from guillotine.tools.local.file_reader import FileReaderLimits, LocalFileReader


def test_list_and_read(tmp_path: Path) -> None:
    (tmp_path / "hello.txt").write_text("Olá Guillotine", encoding="utf-8")
    reader = LocalFileReader(tmp_path)
    assert reader.list_directory()["entries"] == [{"name": "hello.txt", "type": "file"}]
    assert reader.read_file("hello.txt")["content"] == "Olá Guillotine"


def test_search_recursive(tmp_path: Path) -> None:
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "example.py").write_text("first\nneedle here\n", encoding="utf-8")
    result = LocalFileReader(tmp_path).search_files("NEEDLE")
    assert result["matches"] == [
        {"path": "src/example.py", "line": 2, "text": "needle here"}
    ]


@pytest.mark.parametrize(
    "path", ["../secret", "/etc/passwd", "C:/Windows", "..\\secret"]
)
def test_reject_escape(tmp_path: Path, path: str) -> None:
    with pytest.raises((ValueError, PermissionError)):
        LocalFileReader(tmp_path).read_file(path)


def test_reject_symlink_outside(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    try:
        (root / "alias").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation unavailable")
    with pytest.raises(PermissionError):
        LocalFileReader(root).read_file("alias/secret.txt")


def test_limits_and_binary(tmp_path: Path) -> None:
    (tmp_path / "large.txt").write_text("a" * 20, encoding="utf-8")
    (tmp_path / "binary.dat").write_bytes(b"hi\x00there")
    reader = LocalFileReader(tmp_path, FileReaderLimits(max_read_bytes=10))
    with pytest.raises(ValueError, match="limit"):
        reader.read_file("large.txt")
    with pytest.raises(ValueError, match="Binary"):
        reader.read_file("binary.dat")


def test_search_limits(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hit\nhit\n", encoding="utf-8")
    reader = LocalFileReader(tmp_path, FileReaderLimits(max_matches=1))
    result = reader.search_files("hit")
    matches = result["matches"]
    assert isinstance(matches, list)
    assert len(cast(list[object], result["matches"])) == 1
    assert result["truncated"] is True


def test_skip_git_directory(tmp_path: Path) -> None:
    git = tmp_path / ".git"
    git.mkdir()
    (git / "config").write_text("needle", encoding="utf-8")
    assert LocalFileReader(tmp_path).search_files("needle")["matches"] == []

"""Regression tests for junction and symbolic-link path traversal."""

from pathlib import Path

import pytest

from guillotine.tools.local.file_reader import LocalFileReader


def test_read_rejects_intermediate_junction_without_real_windows_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate Windows junctions even on platforms without link privileges."""

    redirected = tmp_path / "alias"
    redirected.mkdir()
    (redirected / "secret.txt").write_text("not readable", encoding="utf-8")
    original = Path.is_junction

    def fake_is_junction(path: Path) -> bool:
        return path == redirected or original(path)

    monkeypatch.setattr(Path, "is_junction", fake_is_junction)
    reader = LocalFileReader(tmp_path)
    with pytest.raises(PermissionError, match="symbolic link or junction"):
        reader.read_file("alias/secret.txt")
    with pytest.raises(PermissionError, match="symbolic link or junction"):
        reader.list_directory("alias")
    assert reader.list_directory()["entries"] == []
    assert reader.search_files("not readable")["matches"] == []


def test_rejects_in_root_symlink_even_if_target_is_inside(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No symlink resolution even when the canonical target is in scope."""

    target = tmp_path / "target.txt"
    target.write_text("sensitive", encoding="utf-8")
    alias = tmp_path / "alias.txt"
    alias.write_text("placeholder", encoding="utf-8")
    original = Path.is_symlink

    def fake_is_symlink(path: Path) -> bool:
        return path == alias or original(path)

    monkeypatch.setattr(Path, "is_symlink", fake_is_symlink)
    reader = LocalFileReader(tmp_path)
    with pytest.raises(PermissionError, match="symbolic link or junction"):
        reader.read_file("alias.txt")
    assert reader.list_directory()["entries"] == [
        {"name": "target.txt", "type": "file"}
    ]

from pathlib import Path

import pytest

from guillotine.core import checkpoint
from guillotine.memory.storage import database


@pytest.fixture
def test_database_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    database_path = tmp_path / "guillotine_test.db"

    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        database_path,
    )

    monkeypatch.setattr(
        checkpoint,
        "DATABASE_PATH",
        database_path,
    )

    return database_path

from dataclasses import FrozenInstanceError

import pytest

from guillotine.core.config import Settings


def test_settings_default_values() -> None:
    settings = Settings.from_env()

    assert settings.BASE_URL == "http://localhost:20128/v1"
    assert isinstance(settings.API_KEY, str)
    assert isinstance(settings.MODEL, str)


def test_settings_reads_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GUILLOTINE_BASE_URL",
        "https://example.com/v1",
    )
    monkeypatch.setenv("GUILLOTINE_API_KEY", "test-api-key")
    monkeypatch.setenv("GUILLOTINE_MODEL", "test-model")

    settings = Settings.from_env()

    assert settings.BASE_URL == "https://example.com/v1"
    assert settings.API_KEY == "test-api-key"
    assert settings.MODEL == "test-model"


def test_settings_rejects_empty_base_url() -> None:
    settings = Settings(
        BASE_URL="",
        API_KEY="test-api-key",
        MODEL="test-model",
    )

    with pytest.raises(
        ValueError,
        match="GUILLOTINE_BASE_URL não configurada",
    ):
        settings.validate()


def test_settings_rejects_empty_model() -> None:
    settings = Settings(
        BASE_URL="http://localhost:20128/v1",
        API_KEY="test-api-key",
        MODEL="",
    )

    with pytest.raises(
        ValueError,
        match="GUILLOTINE_MODEL não configurado",
    ):
        settings.validate()


def test_settings_accepts_empty_api_key() -> None:
    settings = Settings(
        BASE_URL="http://localhost:20128/v1",
        API_KEY="",
        MODEL="test-model",
    )

    settings.validate()


def test_settings_is_immutable() -> None:
    settings = Settings(
        BASE_URL="http://localhost:20128/v1",
        API_KEY="test-api-key",
        MODEL="test-model",
    )

    with pytest.raises(FrozenInstanceError):
        settings.MODEL = "another-model"  # type: ignore[misc]

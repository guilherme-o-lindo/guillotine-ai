"""Propriedades de configuracao com entradas geradas pelo Hypothesis."""

import pytest
from hypothesis import given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

from guillotine.core.config import Settings


@given(model=st.text(max_size=100))
@hypothesis_settings(max_examples=75, deadline=None)
def test_model_is_valid_iff_it_is_not_blank(model: str) -> None:
    config = Settings(
        BASE_URL="http://localhost:20128/v1",
        API_KEY="",
        MODEL=model,
    )

    if model.strip():
        config.validate()
    else:
        with pytest.raises(ValueError, match="GUILLOTINE_MODEL"):
            config.validate()


@given(url=st.text(max_size=100))
@hypothesis_settings(max_examples=75, deadline=None)
def test_base_url_is_valid_iff_it_is_not_blank(url: str) -> None:
    config = Settings(BASE_URL=url, API_KEY="", MODEL="model-test")

    if url.strip():
        config.validate()
    else:
        with pytest.raises(ValueError, match="GUILLOTINE_BASE_URL"):
            config.validate()


@given(timeout=st.floats(min_value=0.000001, max_value=1e6, allow_nan=False))
@hypothesis_settings(max_examples=75, deadline=None)
def test_positive_timeout_is_accepted(timeout: float) -> None:
    Settings(
        BASE_URL="http://localhost:20128/v1",
        API_KEY="",
        MODEL="model-test",
        TIMEOUT_SECONDS=timeout,
    ).validate()


@given(timeout=st.floats(max_value=0, allow_nan=False, allow_infinity=False))
@hypothesis_settings(max_examples=75, deadline=None)
def test_non_positive_timeout_is_rejected(timeout: float) -> None:
    config = Settings(
        BASE_URL="http://localhost:20128/v1",
        API_KEY="",
        MODEL="model-test",
        TIMEOUT_SECONDS=timeout,
    )
    with pytest.raises(ValueError, match="GUILLOTINE_TIMEOUT"):
        config.validate()

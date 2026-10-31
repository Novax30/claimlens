import pytest

from src.config import DEFAULT_TIMEOUT, load_config, validate_timeout


def test_default_timeout_is_thirty_seconds():
    assert DEFAULT_TIMEOUT == 30
    assert load_config({})["timeout"] == 30


def test_positive_timeout_is_accepted():
    assert validate_timeout(10) == 10


def test_zero_and_negative_timeouts_are_rejected():
    with pytest.raises(ValueError):
        validate_timeout(0)
    with pytest.raises(ValueError):
        validate_timeout(-1)


def test_non_integer_timeout_is_rejected():
    with pytest.raises(TypeError):
        validate_timeout("10")

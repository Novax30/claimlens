"""Configuration validation for the sample project."""


DEFAULT_TIMEOUT = 30


def validate_timeout(timeout: int) -> int:
    """Return a valid timeout in seconds."""
    if isinstance(timeout, bool) or not isinstance(timeout, int):
        raise TypeError("timeout must be an integer")
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    return timeout


def load_config(values: dict) -> dict:
    """Load configuration values and apply the default timeout."""
    timeout = values.get("timeout", DEFAULT_TIMEOUT)
    return {"timeout": validate_timeout(timeout)}

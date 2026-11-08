"""
Test helpers from Home Assistant's pytest-homeassistant package.

pytest-homeassistant exists only from Home Assistant 2026.11. Older versions (the
minimum-version CI job) use the discontinued pytest-homeassistant-custom-component.
"""

try:
    from pytest_homeassistant.common import (
        MockConfigEntry,
        async_fire_time_changed,
        async_mock_service,
    )
except ModuleNotFoundError as err:  # Home Assistant 2026.10 and older.
    # A broken pytest_homeassistant install must fail with its own error.
    if err.name != "pytest_homeassistant":
        raise
    from pytest_homeassistant_custom_component.common import (  # pyright: ignore[reportMissingImports]
        MockConfigEntry,
        async_fire_time_changed,
        async_mock_service,
    )

__all__ = [
    "MockConfigEntry",
    "async_fire_time_changed",
    "async_mock_service",
]

"""Diagnostics support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .binary_sensor import DailyScheduleConfigEntry


async def async_get_config_entry_diagnostics(
    _: HomeAssistant, entry: DailyScheduleConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return dict(entry.options)

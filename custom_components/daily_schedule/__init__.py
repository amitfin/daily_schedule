"""Daily schedule integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .binary_sensor import DailyScheduleConfigEntry


async def async_setup_entry(
    hass: HomeAssistant, entry: DailyScheduleConfigEntry
) -> bool:
    """Set up entity from a config entry."""
    await hass.config_entries.async_forward_entry_setups(
        entry, (Platform.BINARY_SENSOR,)
    )
    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))
    return True


async def config_entry_update_listener(
    _: HomeAssistant, entry: DailyScheduleConfigEntry
) -> None:
    """Update listener, called when the config entry options are changed."""
    if entry.runtime_data:
        entry.runtime_data.entity.config_update()


async def async_unload_entry(
    hass: HomeAssistant, entry: DailyScheduleConfigEntry
) -> bool:
    """Unload a config entry."""
    entry.runtime_data = None
    return await hass.config_entries.async_unload_platforms(
        entry, (Platform.BINARY_SENSOR,)
    )

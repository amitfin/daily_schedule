"""Shared test helpers for the daily schedule triggers and conditions tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.const import Platform
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.daily_schedule.const import CONF_SCHEDULE, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

ENTITY_ID = f"{Platform.BINARY_SENSOR}.my_test"


async def setup_entity(hass: HomeAssistant, schedule: list[dict[str, Any]]) -> None:
    """Create a new entity by adding a config entry."""
    config_entry = MockConfigEntry(
        options={CONF_SCHEDULE: schedule}, domain=DOMAIN, title="my_test"
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

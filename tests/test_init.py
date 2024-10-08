"""The tests for the daily schedule integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.daily_schedule.const import (
    CONF_FROM,
    CONF_SCHEDULE,
    CONF_TO,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def test_setup_change_remove_config_entry(hass: HomeAssistant) -> None:
    """Test setting up and removing a config entry."""
    entity_id = f"{Platform.BINARY_SENSOR}.my_test"
    config_entry = MockConfigEntry(domain=DOMAIN, title="My Test", unique_id="1234")

    # Add the config entry.
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check the state and entity registry entry.
    registry = er.async_get(hass)
    assert registry.async_get(entity_id) is not None
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "off"
    assert state.attributes[CONF_SCHEDULE] == []

    # Update the config entry.
    hass.config_entries.async_update_entry(
        config_entry,
        options={CONF_SCHEDULE: [{CONF_FROM: "00:00:00", CONF_TO: "00:00:00"}]},
    )
    await hass.async_block_till_done()

    # Check the updated entity.
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "on"
    assert state.attributes[CONF_SCHEDULE] == [
        {CONF_FROM: "00:00:00", CONF_TO: "00:00:00"},
    ]

    # Remove the config entry.
    assert await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check the state and entity registry entry are removed.
    assert hass.states.get(entity_id) is None
    assert registry.async_get(entity_id) is None

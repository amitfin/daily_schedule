"""Tests for the diagnostics data."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.daily_schedule.const import (
    CONF_FROM,
    CONF_SCHEDULE,
    CONF_TO,
    CONF_UTC,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.typing import ClientSessionGenerator


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test diagnostics."""
    config = {
        CONF_SCHEDULE: [
            {
                CONF_FROM: "01:02:03",
                CONF_TO: "04:05:06",
            },
        ],
        CONF_UTC: True,
    }
    config_entry = MockConfigEntry(
        options=config,
        domain=DOMAIN,
        title="test",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    assert await async_setup_component(hass, "diagnostics", {})
    await hass.async_block_till_done()

    client = await hass_client()
    diagnostics = await client.get(
        f"/api/diagnostics/config_entry/{config_entry.entry_id}"
    )
    assert diagnostics.status == HTTPStatus.OK
    assert config == (await diagnostics.json())["data"]

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

"""Tests for the daily schedule conditions."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

from homeassistant.const import Platform
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.daily_schedule.condition import CONDITIONS, async_get_conditions
from custom_components.daily_schedule.const import CONF_FROM, CONF_TO, DOMAIN
from tests.helpers import ENTITY_ID, setup_entity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def setup_condition_automations(hass: HomeAssistant) -> tuple[list, list]:
    """Create automations gated by is_on/is_off and return their respective calls."""
    is_on_calls = async_mock_service(hass, "test", "is_on")
    is_off_calls = async_mock_service(hass, "test", "is_off")
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": [
                {
                    "trigger": [{"platform": "event", "event_type": "test_event"}],
                    "condition": [
                        {
                            "condition": f"{DOMAIN}.is_on",
                            "target": {"entity_id": ENTITY_ID},
                        }
                    ],
                    "action": [{"service": "test.is_on"}],
                },
                {
                    "trigger": [{"platform": "event", "event_type": "test_event"}],
                    "condition": [
                        {
                            "condition": f"{DOMAIN}.is_off",
                            "target": {"entity_id": ENTITY_ID},
                        }
                    ],
                    "action": [{"service": "test.is_off"}],
                },
            ]
        },
    )
    await hass.async_block_till_done()
    return is_on_calls, is_off_calls


async def test_async_get_conditions(hass: HomeAssistant) -> None:
    """Test the conditions are returned as-is."""
    assert await async_get_conditions(hass) is CONDITIONS


@patch("homeassistant.util.dt.now")
async def test_is_on_and_is_off(mock_now: Mock, hass: HomeAssistant) -> None:
    """Test the conditions match the schedule's on/off state."""
    mock_now.return_value = datetime.datetime.fromisoformat("2000-01-01 23:50:00")
    await setup_entity(hass, [{CONF_FROM: "23:50:00", CONF_TO: "23:55:00"}])

    is_on_calls, is_off_calls = await setup_condition_automations(hass)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    assert len(is_on_calls) == 1
    assert len(is_off_calls) == 0

    mock_now.return_value += datetime.timedelta(minutes=5)
    async_fire_time_changed(hass, mock_now.return_value)
    await hass.async_block_till_done()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    assert len(is_on_calls) == 1
    assert len(is_off_calls) == 1


async def test_ignores_foreign_entities(hass: HomeAssistant) -> None:
    """Test the condition doesn't match an entity not owned by this integration."""
    # A schedule covering the entire day, so the entity is always on.
    await setup_entity(hass, [{CONF_FROM: "00:00:00", CONF_TO: "00:00:00"}])
    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.state == "on"

    foreign_entity_id = f"{Platform.BINARY_SENSOR}.foreign"
    hass.states.async_set(foreign_entity_id, "off")
    await hass.async_block_till_done()

    calls = async_mock_service(hass, "test", "automation")
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": [
                {
                    "trigger": [{"platform": "event", "event_type": "test_event"}],
                    "condition": [
                        {
                            "condition": f"{DOMAIN}.is_off",
                            "target": {"entity_id": [ENTITY_ID, foreign_entity_id]},
                        }
                    ],
                    "action": [{"service": "test.automation"}],
                }
            ]
        },
    )
    await hass.async_block_till_done()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    assert len(calls) == 0

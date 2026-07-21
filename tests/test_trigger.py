"""Tests for the daily schedule triggers."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, Platform
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.daily_schedule.const import CONF_FROM, CONF_TO, DOMAIN
from custom_components.daily_schedule.trigger import TRIGGERS, async_get_triggers
from tests.helpers import ENTITY_ID, setup_entity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def test_async_get_triggers(hass: HomeAssistant) -> None:
    """Test the triggers are returned as-is."""
    assert await async_get_triggers(hass) is TRIGGERS


@patch("homeassistant.util.dt.now")
async def test_turned_on_and_off(mock_now: Mock, hass: HomeAssistant) -> None:
    """Test the triggers fire when a daily schedule turns on and off."""
    mock_now.return_value = datetime.datetime.fromisoformat("2000-01-01 23:50:00")
    await setup_entity(
        hass,
        [
            {CONF_FROM: "23:50:00", CONF_TO: "23:55:00"},
            {CONF_FROM: "00:00:00", CONF_TO: "00:05:00"},
        ],
    )

    on_calls = async_mock_service(hass, "test", "turned_on")
    off_calls = async_mock_service(hass, "test", "turned_off")

    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": [
                {
                    "trigger": [
                        {
                            "platform": f"{DOMAIN}.turned_on",
                            "target": {"entity_id": ENTITY_ID},
                        }
                    ],
                    "action": [{"service": "test.turned_on"}],
                },
                {
                    "trigger": [
                        {
                            "platform": f"{DOMAIN}.turned_off",
                            "target": {"entity_id": ENTITY_ID},
                        }
                    ],
                    "action": [{"service": "test.turned_off"}],
                },
            ]
        },
    )
    await hass.async_block_till_done()

    # 23:50 (on) -> 23:55 (off) -> 00:00 (on) -> 00:05 (off)
    for _ in range(3):
        mock_now.return_value += datetime.timedelta(minutes=5)
        async_fire_time_changed(hass, mock_now.return_value)
        await hass.async_block_till_done()

    assert len(on_calls) == 1
    assert len(off_calls) == 2


@patch("homeassistant.util.dt.now")
async def test_ignores_foreign_entities(mock_now: Mock, hass: HomeAssistant) -> None:
    """Test the trigger doesn't fire for an entity not owned by this integration."""
    mock_now.return_value = datetime.datetime.fromisoformat("2000-01-01 23:50:00")
    await setup_entity(hass, [{CONF_FROM: "23:50:00", CONF_TO: "23:55:00"}])

    foreign_entity_id = f"{Platform.BINARY_SENSOR}.foreign"
    hass.states.async_set(foreign_entity_id, "on")
    await hass.async_block_till_done()

    calls = async_mock_service(hass, "test", "automation")
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": [
                {
                    "trigger": [
                        {
                            "platform": f"{DOMAIN}.turned_off",
                            "target": {"entity_id": [ENTITY_ID, foreign_entity_id]},
                        }
                    ],
                    "action": [{"service": "test.automation"}],
                }
            ]
        },
    )
    await hass.async_block_till_done()

    hass.states.async_set(foreign_entity_id, "off")
    await hass.async_block_till_done()
    assert len(calls) == 0

    mock_now.return_value += datetime.timedelta(minutes=5)
    async_fire_time_changed(hass, mock_now.return_value)
    await hass.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("from_state", [STATE_UNAVAILABLE, STATE_UNKNOWN])
async def test_ignores_unavailable_and_unknown_from_state(
    hass: HomeAssistant, from_state: str
) -> None:
    """Test the trigger doesn't fire when the origin state is unavailable/unknown."""
    await setup_entity(hass, [{CONF_FROM: "00:00:00", CONF_TO: "00:00:00"}])

    calls = async_mock_service(hass, "test", "automation")
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": [
                {
                    "trigger": [
                        {
                            "platform": f"{DOMAIN}.turned_on",
                            "target": {"entity_id": ENTITY_ID},
                        }
                    ],
                    "action": [{"service": "test.automation"}],
                }
            ]
        },
    )
    await hass.async_block_till_done()

    hass.states.async_set(ENTITY_ID, from_state)
    await hass.async_block_till_done()
    hass.states.async_set(ENTITY_ID, "on")
    await hass.async_block_till_done()
    assert len(calls) == 0

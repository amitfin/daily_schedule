"""The tests for the daily schedule sensor component."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytz
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, Platform
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.daily_schedule.const import (
    ATTR_NEXT_TOGGLE,
    ATTR_NEXT_TOGGLES,
    CONF_FROM,
    CONF_SCHEDULE,
    CONF_TO,
    CONF_UTC,
    DOMAIN,
    SERVICE_SET,
)

if TYPE_CHECKING:
    from freezegun.api import FrozenDateTimeFactory
    from homeassistant.core import HomeAssistant


async def setup_entity(
    hass: HomeAssistant,
    name: str,
    schedule: list[dict[str, Any]],
    utc: bool = False,  # noqa: FBT001, FBT002
) -> None:
    """Create a new entity by adding a config entry."""
    config_entry = MockConfigEntry(
        options={CONF_SCHEDULE: schedule, CONF_UTC: utc},
        domain=DOMAIN,
        title=name,
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


async def async_cleanup(hass: HomeAssistant) -> None:
    """Delete all config entries."""
    for config_entry in hass.config_entries.async_entries(DOMAIN):
        assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize(
    "schedule",
    [
        [],
        [
            {
                CONF_FROM: "01:02:03",
                CONF_TO: "04:05:06",
            },
        ],
        [
            {
                CONF_FROM: "04:05:06",
                CONF_TO: "01:02:03",
            },
        ],
        [
            {
                CONF_FROM: "00:00:00",
                CONF_TO: "00:00:00",
            },
        ],
        [
            {
                CONF_FROM: "07:08:09",
                CONF_TO: "10:11:12",
            },
            {
                CONF_FROM: "01:02:03",
                CONF_TO: "04:05:06",
            },
        ],
        [
            {
                CONF_FROM: "10:11:12",
                CONF_TO: "01:02:03",
            },
            {
                CONF_FROM: "01:02:03",
                CONF_TO: "04:05:06",
            },
        ],
    ],
    ids=[
        "empty",
        "single",
        "overnight",
        "entire_day",
        "multiple",
        "adjusted",
    ],
)
async def test_new_sensor(hass: HomeAssistant, schedule: list[dict[str, Any]]) -> None:
    """Test new sensor."""
    entity_id = f"{Platform.BINARY_SENSOR}.my_test"
    await setup_entity(hass, "My Test", schedule)
    schedule.sort(key=lambda time_range: time_range[CONF_FROM])
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes[CONF_SCHEDULE] == schedule
    await async_cleanup(hass)


@patch("homeassistant.util.dt.now")
async def test_state(mock_now: Mock, hass: HomeAssistant) -> None:
    """Test state attribute."""
    mock_now.return_value = datetime.datetime.fromisoformat("2000-01-01 23:50:00")

    entity_id = f"{Platform.BINARY_SENSOR}.my_test"
    await setup_entity(
        hass,
        "My Test",
        [
            {CONF_FROM: "23:50:00", CONF_TO: "23:55:00"},
            {CONF_FROM: "00:00:00", CONF_TO: "00:05:00"},
        ],
    )

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON

    state = STATE_OFF
    for _ in range(3):
        mock_now.return_value += datetime.timedelta(minutes=5)
        async_fire_time_changed(hass, mock_now.return_value)
        await hass.async_block_till_done()
        state_obj = hass.states.get(entity_id)
        assert state_obj
        assert state_obj.state == state
        state = STATE_ON if state == STATE_OFF else STATE_OFF

    await async_cleanup(hass)


@pytest.mark.parametrize(
    "schedule",
    [
        [
            {
                CONF_FROM: "00:00:00",
                CONF_TO: "00:00:00",
            },
        ],
        [
            {
                CONF_FROM: "07:00:00",
                CONF_TO: "07:00:00",
            },
        ],
        [
            {
                CONF_FROM: "17:00:00",
                CONF_TO: "07:00:00",
            },
            {
                CONF_FROM: "07:00:00",
                CONF_TO: "17:00:00",
            },
        ],
    ],
    ids=["midnight", "one", "two"],
)
async def test_entire_day(hass: HomeAssistant, schedule: list[dict[str, Any]]) -> None:
    """Test entire day schedule."""
    entity_id = f"{Platform.BINARY_SENSOR}.my_test"
    await setup_entity(hass, "My Test", schedule)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert not state.attributes[ATTR_NEXT_TOGGLE]


@patch("homeassistant.util.dt.now")
@patch("homeassistant.helpers.event.async_track_point_in_time")
async def test_next_update(
    async_track_point_in_time: AsyncMock, mock_now: Mock, hass: HomeAssistant
) -> None:
    """Test next update time."""
    mock_now.return_value = datetime.datetime.fromisoformat("2000-01-01")

    in_5_minutes = mock_now.return_value + datetime.timedelta(minutes=5)
    in_10_minutes = mock_now.return_value + datetime.timedelta(minutes=10)
    previous_5_minutes = mock_now.return_value + datetime.timedelta(minutes=-5)
    previous_10_minutes = mock_now.return_value + datetime.timedelta(minutes=-10)

    # No schedule => no updates.
    assert async_track_point_in_time.call_count == 0

    # Inside a time range.
    await setup_entity(
        hass,
        "Test1",
        [
            {
                CONF_FROM: previous_5_minutes.time().isoformat(),
                CONF_TO: in_5_minutes.time().isoformat(),
            }
        ],
    )
    state = hass.states.get(f"{Platform.BINARY_SENSOR}.test1")
    assert state
    assert state.state == STATE_ON
    next_update = async_track_point_in_time.call_args[0][2]
    assert next_update == in_5_minutes
    state = hass.states.get(f"{Platform.BINARY_SENSOR}.test1")
    assert state
    assert state.attributes[ATTR_NEXT_TOGGLE] == in_5_minutes
    assert state.attributes[ATTR_NEXT_TOGGLES] == [
        in_5_minutes,
        previous_5_minutes + datetime.timedelta(days=1),
        in_5_minutes + datetime.timedelta(days=1),
        previous_5_minutes + datetime.timedelta(days=2),
    ]

    # After all ranges.
    await setup_entity(
        hass,
        "Test2",
        [
            {
                CONF_FROM: previous_10_minutes.time().isoformat(),
                CONF_TO: previous_5_minutes.time().isoformat(),
            }
        ],
    )
    state = hass.states.get(f"{Platform.BINARY_SENSOR}.test2")
    assert state
    assert state.state == STATE_OFF
    expected_next_update = previous_10_minutes + datetime.timedelta(days=1)
    next_update = async_track_point_in_time.call_args[0][2]
    assert next_update == expected_next_update
    state = hass.states.get(f"{Platform.BINARY_SENSOR}.test2")
    assert state
    assert state.attributes[ATTR_NEXT_TOGGLE] == expected_next_update
    assert state.attributes[ATTR_NEXT_TOGGLES] == [
        expected_next_update,
        previous_5_minutes + datetime.timedelta(days=1),
        expected_next_update + datetime.timedelta(days=1),
        previous_5_minutes + datetime.timedelta(days=2),
    ]

    # Before any range.
    await setup_entity(
        hass,
        "Test3",
        [
            {
                CONF_FROM: in_5_minutes.time().isoformat(),
                CONF_TO: in_10_minutes.time().isoformat(),
            }
        ],
    )
    state = hass.states.get(f"{Platform.BINARY_SENSOR}.test3")
    assert state
    assert state.state == STATE_OFF
    next_update = async_track_point_in_time.call_args[0][2]
    assert next_update == in_5_minutes
    assert state.attributes[ATTR_NEXT_TOGGLE] == in_5_minutes
    assert state.attributes[ATTR_NEXT_TOGGLES] == [
        in_5_minutes,
        in_10_minutes,
        in_5_minutes + datetime.timedelta(days=1),
        in_10_minutes + datetime.timedelta(days=1),
    ]
    await async_cleanup(hass)


async def test_set(hass: HomeAssistant) -> None:
    """Test set service."""
    schedule1 = [{CONF_FROM: "01:02:03", CONF_TO: "04:05:06"}]
    schedule2 = [{CONF_FROM: "07:08:09", CONF_TO: "10:11:12"}]
    entity_id = f"{Platform.BINARY_SENSOR}.my_test"

    await setup_entity(hass, "My Test", schedule1)
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes[CONF_SCHEDULE] == schedule1

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET,
        {CONF_SCHEDULE: schedule2},
        target={ATTR_ENTITY_ID: entity_id},
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes[CONF_SCHEDULE] == schedule2
    await async_cleanup(hass)


@pytest.mark.parametrize(
    "schedule",
    [
        [
            {
                CONF_FROM: "04:05:05",
                CONF_TO: "07:08:09",
            },
            {
                CONF_FROM: "01:02:03",
                CONF_TO: "04:05:06",
            },
        ],
        [
            {
                CONF_FROM: "07:08:09",
                CONF_TO: "01:02:04",
            },
            {
                CONF_FROM: "01:02:03",
                CONF_TO: "04:05:06",
            },
        ],
    ],
    ids=["overlap", "overnight_overlap"],
)
async def test_invalid_set(hass: HomeAssistant, schedule: list[dict[str, Any]]) -> None:
    """Test invalid input to set method."""
    entity_id = f"{Platform.BINARY_SENSOR}.my_test"
    await setup_entity(hass, "My Test", [])
    with pytest.raises(ValueError) as excinfo:  # noqa: PT011
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET,
            {ATTR_ENTITY_ID: entity_id, CONF_SCHEDULE: schedule},
            blocking=True,
        )
    assert "overlap" in str(excinfo.value)
    await async_cleanup(hass)


@pytest.mark.parametrize(
    "utc",
    [True, False],
    ids=["utc", "local"],
)
async def test_utc(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    utc: bool,  # noqa: FBT001
) -> None:
    """Test utc schedule."""
    utc_time = datetime.datetime(2023, 5, 30, 12, tzinfo=pytz.utc)  # 12pm
    local_time = utc_time.astimezone(pytz.timezone("US/Pacific"))  # 4am
    offset = utc_time.timestamp() - local_time.replace(tzinfo=None).timestamp()  # 8h
    freezer.move_to(local_time)
    entity_id = f"{Platform.BINARY_SENSOR}.my_test"
    await setup_entity(
        hass,
        "My Test",
        [
            {
                CONF_FROM: "12:00:00",
                CONF_TO: "12:00:01",
            },
        ],
        utc,
    )
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON if utc else STATE_OFF
    next_toggle_timestamp = state.attributes[ATTR_NEXT_TOGGLE].timestamp()
    assert next_toggle_timestamp == local_time.timestamp() + (1 if utc else offset)
    if utc:
        assert state.attributes[ATTR_NEXT_TOGGLES][0].timestamp() == (
            local_time.timestamp() + 1
        )
        assert state.attributes[ATTR_NEXT_TOGGLES][1].timestamp() == (
            (local_time + datetime.timedelta(days=1)).timestamp()
        )
        assert state.attributes[ATTR_NEXT_TOGGLES][2].timestamp() == (
            (local_time + datetime.timedelta(days=1)).timestamp() + 1
        )
        assert state.attributes[ATTR_NEXT_TOGGLES][3].timestamp() == (
            (local_time + datetime.timedelta(days=2)).timestamp()
        )
    else:
        assert state.attributes[ATTR_NEXT_TOGGLES][0].timestamp() == (
            local_time.timestamp() + offset
        )
        assert state.attributes[ATTR_NEXT_TOGGLES][1].timestamp() == (
            local_time.timestamp() + offset + 1
        )
        assert state.attributes[ATTR_NEXT_TOGGLES][2].timestamp() == (
            (local_time + datetime.timedelta(days=1)).timestamp() + offset
        )
        assert state.attributes[ATTR_NEXT_TOGGLES][3].timestamp() == (
            (local_time + datetime.timedelta(days=1)).timestamp() + offset + 1
        )
    await async_cleanup(hass)

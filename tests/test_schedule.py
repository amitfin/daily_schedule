"""The tests for the schedule class."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import pytest
from homeassistant.exceptions import IntegrationError

from custom_components.daily_schedule.const import (
    CONF_DISABLED,
    CONF_FROM,
    CONF_TO,
    SUNRISE_SYMBOL,
    SUNSET_SYMBOL,
)
from custom_components.daily_schedule.schedule import (
    Schedule,
    TimeRange,
    TimeRangeConfig,
)

if TYPE_CHECKING:
    from freezegun.api import FrozenDateTimeFactory
    from homeassistant.core import HomeAssistant


@pytest.mark.parametrize(
    ("from1", "to1", "from2", "to2", "result"),
    [
        ("01:00", "02:00", "01:00", "02:00", False),
        ("01:01", "02:00", "01:00", "02:00", True),
        ("01:00", "02:01", "01:00", "02:00", True),
        ("01:00", "02:00", "01:01", "02:00", False),
    ],
    ids=["equal", "start", "length", "smaller"],
)
def test_greater_operator(
    from1: str,
    to1: str,
    from2: str,
    to2: str,
    result: bool,  # noqa: FBT001
) -> None:
    """Test comparison of TimeRange."""
    assert (
        TimeRange(datetime.time.fromisoformat(from1), datetime.time.fromisoformat(to1))
        > TimeRange(
            datetime.time.fromisoformat(from2), datetime.time.fromisoformat(to2)
        )
    ) is result


def test_sort() -> None:
    """Test sorting of TimeRange."""
    time_ranges = [
        TimeRange(
            datetime.time.fromisoformat("02:00"), datetime.time.fromisoformat("03:00")
        ),
        TimeRange(
            datetime.time.fromisoformat("01:00"), datetime.time.fromisoformat("01:30")
        ),
        TimeRange(
            datetime.time.fromisoformat("01:00"), datetime.time.fromisoformat("02:00")
        ),
    ]
    time_ranges.sort()
    assert time_ranges == [
        TimeRange(
            datetime.time.fromisoformat("01:00"), datetime.time.fromisoformat("01:30")
        ),
        TimeRange(
            datetime.time.fromisoformat("01:00"), datetime.time.fromisoformat("02:00")
        ),
        TimeRange(
            datetime.time.fromisoformat("02:00"), datetime.time.fromisoformat("03:00")
        ),
    ]


@pytest.mark.parametrize(
    ("start", "end", "time", "disabled", "result"),
    [
        ("05:00", "10:00", "05:00", False, True),
        ("05:00", "10:00", "10:00", False, False),
        ("22:00", "05:00", "23:00", False, True),
        ("22:00", "05:00", "04:00", False, True),
        ("22:00", "05:00", "12:00", False, False),
        ("00:00", "00:00", "00:00", False, True),
        ("00:00", "00:00", "00:00", True, False),
    ],
    ids=[
        "contained",
        "not contained",
        "cross day night",
        "cross day morning",
        "cross day not contained",
        "entire day",
        "entire day disabled",
    ],
)
def test_time_range(  # noqa: PLR0913
    hass: HomeAssistant,
    start: str,
    end: str,
    time: str,
    disabled: bool,  # noqa: FBT001
    result: bool,  # noqa: FBT001
) -> None:
    """Test for TimeRange class."""
    assert (
        TimeRangeConfig(hass, start, end, disabled).containing(
            datetime.time.fromisoformat(time)
        )
        is result
    )


@pytest.mark.parametrize(
    ("from_", "to", "from_absolute", "to_absolute", "from_string", "to_string"),
    [
        (
            SUNRISE_SYMBOL,
            SUNSET_SYMBOL,
            "05:54:37",
            "17:46:10",
            SUNRISE_SYMBOL,
            SUNSET_SYMBOL,
        ),
        ("↑+10", "↓-10", "06:04:37", "17:36:10", "↑+10", "↓-10"),
        ("↑+0", "↓-0", "05:54:37", "17:46:10", SUNRISE_SYMBOL, SUNSET_SYMBOL),
    ],
    ids=[
        "sunrise to sunset",
        "offsets",
        "zero offset",
    ],
)
async def test_dynamic_range(  # noqa: PLR0913
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    from_: str,
    to: str,
    from_absolute: str,
    to_absolute: str,
    from_string: str,
    to_string: str,
) -> None:
    """Test dynamic from and to."""
    freezer.move_to("2025-03-12T00:00:00")
    hass.config.latitude = 32.072
    hass.config.longitude = 34.879
    await hass.config.async_set_time_zone("Asia/Jerusalem")
    test = TimeRangeConfig(hass, from_, to, False)  # noqa: FBT003
    assert test.to_dict() == {CONF_FROM: from_string, CONF_TO: to_string}
    assert test.to_dict_absolute() == {CONF_FROM: from_absolute, CONF_TO: to_absolute}


@patch("homeassistant.helpers.sun.get_astral_event_date", return_value=None)
def test_sun_not_resolvable(_: Mock, hass: HomeAssistant) -> None:  # noqa: PT019
    """Test error when sun is not resolvable."""
    with pytest.raises(IntegrationError):
        TimeRangeConfig(hass, SUNRISE_SYMBOL, SUNSET_SYMBOL, False)  # noqa: FBT003


@pytest.mark.parametrize(
    "param",
    [
        {CONF_FROM: "05:00:00", CONF_TO: "10:00:00"},
        {CONF_FROM: "10:00:00", CONF_TO: "05:00:00", CONF_DISABLED: True},
        {CONF_FROM: "05:00:00", CONF_TO: "05:00:00"},
    ],
    ids=[
        "regular",
        "cross day",
        "entire day",
    ],
)
def test_time_range_to_dict(hass: HomeAssistant, param: dict[str, Any]) -> None:
    """Test TimeRange to_dict."""
    assert (
        TimeRangeConfig(
            hass, param[CONF_FROM], param[CONF_TO], param.get(CONF_DISABLED, False)
        ).to_dict()
        == param
    )


@pytest.mark.parametrize(
    ("schedule", "time", "result"),
    [
        ([], "05:00", False),
        ([{CONF_FROM: "05:00", CONF_TO: "10:00"}], "05:00", True),
        ([{CONF_FROM: "05:00", CONF_TO: "10:00"}], "10:00", False),
        (
            [
                {CONF_FROM: "22:00", CONF_TO: "00:00"},
                {CONF_FROM: "05:00", CONF_TO: "10:00"},
            ],
            "23:00",
            True,
        ),
        ([{CONF_FROM: "00:00", CONF_TO: "00:00", CONF_DISABLED: True}], "12:00", False),
    ],
    ids=[
        "empty",
        "contained",
        "not contained",
        "2 ranges contained",
        "disabled range",
    ],
)
def test_schedule_containing(
    hass: HomeAssistant,
    schedule: list[dict[str, Any]],
    time: str,
    result: bool,  # noqa: FBT001
) -> None:
    """Test containing method of Schedule."""
    assert (
        Schedule(hass, schedule).containing(datetime.time.fromisoformat(time)) is result
    )


@pytest.mark.parametrize(
    ("schedule", "on", "off"),
    [
        (
            [
                {
                    CONF_FROM: "01:02:03",
                    CONF_TO: "04:05:06",
                },
                {
                    CONF_FROM: "07:08:09",
                    CONF_TO: "07:08:09",
                },
                {
                    CONF_FROM: "10:11:12",
                    CONF_TO: "10:11:13",
                },
            ],
            "05:06:07",
            None,
        ),
        (
            [
                {
                    CONF_FROM: "04:05:06",
                    CONF_TO: "01:02:03",
                },
                {
                    CONF_FROM: "07:08:09",
                    CONF_TO: "10:11:12",
                },
            ],
            "01:00:00",
            "03:00:00",
        ),
        (
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
            "02:00:00",
            "08:00:00",
        ),
        (
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
            "00:00:00",
            "05:00:00",
        ),
    ],
    ids=["wrap whole", "warp", "overlap", "overnight_overlap"],
)
def test_complex_schedule(
    hass: HomeAssistant, schedule: list[dict[str, Any]], on: str | None, off: str | None
) -> None:
    """Test complex schedule."""
    test = Schedule(hass, schedule)
    if on is not None:
        assert test.containing(datetime.time.fromisoformat(on)) is True
    if off is not None:
        assert test.containing(datetime.time.fromisoformat(off)) is False


@pytest.mark.parametrize(
    "schedule",
    [
        [
            {
                CONF_FROM: "01:00:00",
                CONF_TO: "02:00:00",
            },
        ],
        [
            {
                CONF_FROM: "03:00:00",
                CONF_TO: "04:00:00",
                CONF_DISABLED: True,
            },
            {
                CONF_FROM: "01:00:00",
                CONF_TO: "02:00:00",
            },
        ],
    ],
    ids=["one", "two"],
)
def test_to_list(hass: HomeAssistant, schedule: list[dict[str, Any]]) -> None:
    """Test schedule to string list function."""
    str_list = Schedule(hass, schedule).to_list()
    schedule.sort(key=lambda time_range: time_range[CONF_FROM])
    assert str_list == schedule


def test_merge(hass: HomeAssistant) -> None:
    """Test merging logic."""
    assert Schedule(
        hass,
        [
            {CONF_FROM: "22:00:00", CONF_TO: "02:00:00"},
            {CONF_FROM: "19:00:00", CONF_TO: "22:00:00"},
        ],
    ).to_list_absolute() == [{CONF_FROM: "19:00:00", CONF_TO: "02:00:00"}]

    assert Schedule(
        hass,
        [
            {CONF_FROM: "01:00:00", CONF_TO: "05:00:00"},
            {CONF_FROM: "23:00:00", CONF_TO: "01:00:00"},
            {CONF_FROM: "05:00:00", CONF_TO: "23:00:00"},
        ],
    ).to_list_absolute() == [{CONF_FROM: "00:00:00", CONF_TO: "00:00:00"}]


@pytest.mark.parametrize(
    ("schedule", "next_update_sec_offset"),
    [
        ([(-5, 5, False)], 5),
        ([(-10, -5, False)], datetime.timedelta(days=1).total_seconds() - 10),
        ([(5, 10, False)], 5),
        ([(0, 0, False)], None),
        ([(100, 200, False), (200, 100, False)], None),
        ([(-100, 100, False), (100, 200, False)], 200),
        ([(-100, 100, True), (100, 200, False)], 100),
        ([(80, 100, False), (70, 90, False), (0, 80, False)], 100),
        ([(200, 50, False), (20, 100, False)], 100),
    ],
    ids=[
        "inside range",
        "after all ranges",
        "before all ranges",
        "entire_day_1_range",
        "entire_day_2_ranges",
        "adjusted_ranges",
        "disabled_range",
        "overlapping_ranges",
        "overlap_and_wrap",
    ],
)
def test_next_update(
    hass: HomeAssistant,
    schedule: list[Any],
    next_update_sec_offset: int | None,
) -> None:
    """Test next update logic."""
    now = datetime.datetime.fromisoformat("2000-01-01")
    assert Schedule(
        hass,
        [
            {
                CONF_FROM: (now + datetime.timedelta(seconds=from_sec_offset))
                .time()
                .isoformat(),
                CONF_TO: (now + datetime.timedelta(seconds=to_sec_offset))
                .time()
                .isoformat(),
                CONF_DISABLED: disabled,
            }
            for (from_sec_offset, to_sec_offset, disabled) in schedule
        ],
    ).next_update(now) == (
        now + datetime.timedelta(seconds=next_update_sec_offset)
        if next_update_sec_offset is not None
        else None
    )


def test_next_updates(
    hass: HomeAssistant,
) -> None:
    """Test next updates."""
    now = datetime.datetime.fromisoformat("2000-01-01")
    assert Schedule(
        hass,
        [
            {
                CONF_FROM: "01:00",
                CONF_TO: "02:00",
            },
            {
                CONF_FROM: "03:00",
                CONF_TO: "04:00",
            },
        ],
    ).next_updates(now, 5) == [
        now + datetime.timedelta(hours=1),
        now + datetime.timedelta(hours=2),
        now + datetime.timedelta(hours=3),
        now + datetime.timedelta(hours=4),
        now + datetime.timedelta(days=1, hours=1),
    ]

"""The tests for the schedule class."""
from __future__ import annotations

import datetime

import pytest

from custom_components.daily_schedule.const import CONF_TO, CONF_FROM
from custom_components.daily_schedule.schedule import Schedule, TimeRange


@pytest.mark.parametrize(
    ["start", "end", "time", "result"],
    [
        ("05:00", "10:00", "05:00", True),
        ("05:00", "10:00", "10:00", False),
        ("22:00", "05:00", "23:00", True),
        ("22:00", "05:00", "04:00", True),
        ("22:00", "05:00", "12:00", False),
        ("00:00", "00:00", "00:00", True),
    ],
    ids=[
        "contained",
        "not contained",
        "cross day night",
        "cross day morning",
        "cross day not contained",
        "entire day",
    ],
)
def test_time_range(start: str, end: str, time: str, result: bool):
    """Test for TimeRange class."""
    assert TimeRange(start, end).containing(datetime.time.fromisoformat(time)) is result


@pytest.mark.parametrize(
    [
        "param",
    ],
    [
        ({CONF_FROM: "05:00:00", CONF_TO: "10:00:00"},),
        ({CONF_FROM: "10:00:00", CONF_TO: "05:00:00"},),
        ({CONF_FROM: "05:00:00", CONF_TO: "05:00:00"},),
    ],
    ids=[
        "regular",
        "cross day",
        "entire day",
    ],
)
def test_time_range_to_dict(param: dict[str, str]):
    """Test TimeRange to_dict."""
    assert TimeRange(param[CONF_FROM], param[CONF_TO]).to_dict() == param


@pytest.mark.parametrize(
    ["schedule", "time", "result"],
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
    ],
    ids=[
        "empty",
        "contained",
        "not contained",
        "2 ranges contained",
    ],
)
def test_schedule_containing(schedule: list[dict[str, str]], time: str, result: bool):
    """Test containing method of Schedule."""
    assert Schedule(schedule).containing(datetime.time.fromisoformat(time)) is result


@pytest.mark.parametrize(
    ["schedule", "reason"],
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
            "zero",
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
            "negative",
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
            "overlap",
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
            "overlap",
        ),
    ],
    ids=["zero length", "negative lenght", "overlap", "overnight_overlap"],
)
def test_invalid(schedule: list[dict[str, str]], reason: str):
    """Test invalid schedule."""
    with pytest.raises(ValueError) as excinfo:
        Schedule(schedule)
    assert reason in str(excinfo.value)


@pytest.mark.parametrize(
    ["schedule"],
    [
        (
            [
                {
                    CONF_FROM: "01:00:00",
                    CONF_TO: "02:00:00",
                },
            ],
        ),
        (
            [
                {
                    CONF_FROM: "03:00:00",
                    CONF_TO: "04:00:00",
                },
                {
                    CONF_FROM: "01:00:00",
                    CONF_TO: "02:00:00",
                },
            ],
        ),
    ],
    ids=["one", "two"],
)
def test_to_list(schedule: list[dict[str, str]]) -> None:
    """Test schedule to string list function."""
    str_list = Schedule(schedule).to_list()
    schedule.sort(key=lambda time_range: time_range[CONF_FROM])
    assert str_list == schedule


def test_to_str() -> None:
    """Test schedule to string function."""
    schedule = Schedule(
        [
            {
                CONF_FROM: "03:00:00",
                CONF_TO: "04:00:00",
            },
            {
                CONF_FROM: "01:00:00",
                CONF_TO: "02:00:00",
            },
        ]
    )
    assert schedule.to_str() == ", ".join(
        [
            f"{time_period[CONF_FROM]} - {time_period[CONF_TO]}"
            for time_period in schedule.to_list()
        ]
    )


@pytest.mark.parametrize(
    ["from_sec_offset", "to_sec_offset", "next_update_sec_offset"],
    [
        (-5, 5, 5),
        (-10, -5, datetime.timedelta(days=1).total_seconds() - 10),
        (5, 10, 5),
    ],
    ids=["inside range", "after all rangess", "before all ranges"],
)
def test_next_update(
    from_sec_offset: int,
    to_sec_offset: int,
    next_update_sec_offset: int,
) -> None:
    """Test next update logic."""
    now = datetime.datetime.fromisoformat("2000-01-01")
    assert Schedule(
        [
            {
                CONF_FROM: (now + datetime.timedelta(seconds=from_sec_offset))
                .time()
                .isoformat(),
                CONF_TO: (now + datetime.timedelta(seconds=to_sec_offset))
                .time()
                .isoformat(),
            }
        ]
    ).next_update(now) == now + datetime.timedelta(seconds=next_update_sec_offset)

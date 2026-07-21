"""Provides conditions for daily schedules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.helpers.automation import DomainSpec
from homeassistant.helpers.condition import Condition, EntityStateConditionBase

from .entity_filter import DailyScheduleEntityFilter

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def _make_condition(state: str) -> type[EntityStateConditionBase]:
    """Create a daily schedule condition for entities matching the given state."""

    class DailyScheduleCondition(DailyScheduleEntityFilter, EntityStateConditionBase):
        """Condition for a daily schedule matching a specific state."""

        _domain_specs = {BINARY_SENSOR_DOMAIN: DomainSpec()}  # noqa: RUF012
        _states = {state}  # noqa: RUF012

    return DailyScheduleCondition


CONDITIONS: dict[str, type[Condition]] = {
    "is_off": _make_condition(STATE_OFF),
    "is_on": _make_condition(STATE_ON),
}


async def async_get_conditions(_hass: HomeAssistant) -> dict[str, type[Condition]]:
    """Return the daily schedule conditions."""
    return CONDITIONS

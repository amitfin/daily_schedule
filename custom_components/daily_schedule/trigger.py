"""Provides triggers for daily schedules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.helpers.automation import DomainSpec
from homeassistant.helpers.trigger import EntityTargetStateTriggerBase, Trigger

from .entity_filter import DailyScheduleEntityFilter

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def _make_trigger(to_state: str) -> type[EntityTargetStateTriggerBase]:
    """Create a daily schedule trigger for entities reaching the given state."""

    class DailyScheduleTrigger(DailyScheduleEntityFilter, EntityTargetStateTriggerBase):
        """Trigger for a daily schedule reaching a specific state."""

        _domain_specs = {BINARY_SENSOR_DOMAIN: DomainSpec()}  # noqa: RUF012
        _to_states = {to_state}  # noqa: RUF012

    return DailyScheduleTrigger


TRIGGERS: dict[str, type[Trigger]] = {
    "turned_on": _make_trigger(STATE_ON),
    "turned_off": _make_trigger(STATE_OFF),
}


async def async_get_triggers(_hass: HomeAssistant) -> dict[str, type[Trigger]]:
    """Return the triggers for daily schedules."""
    return TRIGGERS

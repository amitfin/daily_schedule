"""Support for representing daily schedule as binary sensors."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_platform
from homeassistant.helpers import event as event_helper

from .const import (
    ATTR_EFFECTIVE_SCHEDULE,
    ATTR_NEXT_TOGGLE,
    ATTR_NEXT_TOGGLES,
    CONF_DISABLED,
    CONF_FROM,
    CONF_SCHEDULE,
    CONF_TO,
    CONF_UTC,
    NEXT_TOGGLES_COUNT,
    SERVICE_SET,
    SUNRISE_SYMBOL,
    SUNSET_SYMBOL,
)
from .schedule import Schedule

if TYPE_CHECKING:
    from collections.abc import Callable, MutableMapping

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


def remove_micros_and_tz(time: datetime.time) -> str:
    """Remove microseconds and timezone from a time object."""
    return time.replace(microsecond=0, tzinfo=None).isoformat()


def dynamic_time(value: Any) -> str:
    """Validate and transform a time string to a time object."""
    time = cv.string(value)
    if not time.startswith((SUNRISE_SYMBOL, SUNSET_SYMBOL)):
        error = (
            f"should begin with sunrise symbol ({SUNRISE_SYMBOL}) "
            f"or sunset symbol ({{SUNSET_SYMBOL}})"
        )
        raise vol.Invalid(error)
    if len(time) > 1:
        vol.Coerce(int)(time[1:])
    return time


ENTRY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_FROM): vol.Any(
            vol.All(cv.time, remove_micros_and_tz), dynamic_time
        ),
        vol.Required(CONF_TO): vol.Any(
            vol.All(cv.time, remove_micros_and_tz), dynamic_time
        ),
        vol.Optional(CONF_DISABLED): cv.boolean,
    },
    extra=vol.ALLOW_EXTRA,
)
SERVICE_SET_SCHEMA = cv.make_entity_service_schema(
    {
        vol.Required(CONF_SCHEDULE): vol.All(cv.ensure_list, [ENTRY_SCHEMA]),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize config entry."""
    async_add_entities([DailyScheduleSensor(hass, config_entry)])
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(SERVICE_SET, SERVICE_SET_SCHEMA, "async_set")


class DailyScheduleSensor(BinarySensorEntity):
    """Representation of a daily schedule sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:timetable"
    _unrecorded_attributes = frozenset(
        {ATTR_NEXT_TOGGLE, ATTR_NEXT_TOGGLES, ATTR_EFFECTIVE_SCHEDULE, CONF_SCHEDULE}
    )

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize object with defaults."""
        self._hass = hass
        self._config_entry = config_entry
        self._attr_name = config_entry.title
        self._attr_unique_id = config_entry.entry_id
        self._schedule: Schedule = Schedule(
            hass, config_entry.options.get(CONF_SCHEDULE, [])
        )
        self._attr_extra_state_attributes: MutableMapping[str, Any] = {
            CONF_SCHEDULE: self._schedule.to_list(),
            ATTR_EFFECTIVE_SCHEDULE: self._schedule.to_list_absolute(),
        }
        self._is_dynamic = self._schedule.is_dynamic()
        self._utc = config_entry.options.get(CONF_UTC, False)
        self._unsub_update: Callable[[], None] | None = None

    def _now(self) -> datetime.datetime:
        """Return the current time either as local or UTC, based on configuration."""
        return dt_util.now() if not self._utc else dt_util.utcnow()

    @property
    def is_on(self) -> bool:
        """Return True is sensor is on."""
        return self._schedule.containing(self._now().time())

    @callback
    def _clean_up_listener(self) -> None:
        """Remove the timer."""
        if self._unsub_update is not None:
            self._unsub_update()
            self._unsub_update = None

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(self._clean_up_listener)
        self._update_state()

    async def async_set(self, schedule: list[dict[str, Any]]) -> None:
        """Update the config entry with the new list (non-admin support)."""
        self.hass.config_entries.async_update_entry(
            self._config_entry,
            options={
                **self._config_entry.options,
                CONF_SCHEDULE: Schedule(self._hass, schedule).to_list(),
            },
        )

    @callback
    def _update_state(self, _: datetime.datetime | None = None) -> None:
        """Update the state & attributes and schedule next update."""
        self._unsub_update = None

        if self._is_dynamic:
            # Re-resolve sunrise/sunset times.
            self._schedule = Schedule(
                self._hass, self._attr_extra_state_attributes[CONF_SCHEDULE]
            )
            self._attr_extra_state_attributes[ATTR_EFFECTIVE_SCHEDULE] = (
                self._schedule.to_list_absolute()
            )

        next_toggles = self._schedule.next_updates(self._now(), NEXT_TOGGLES_COUNT)
        next_update = next_toggles[0] if len(next_toggles) > 0 else None
        self._attr_extra_state_attributes[ATTR_NEXT_TOGGLE] = next_update
        self._attr_extra_state_attributes[ATTR_NEXT_TOGGLES] = next_toggles

        self.async_write_ha_state()

        tomorrow = (
            dt_util.now().replace(hour=0, minute=0, second=0, microsecond=0)
            + datetime.timedelta(days=1)
            if self._is_dynamic
            else None
        )

        if not next_update or (tomorrow and tomorrow < next_update):
            next_update = tomorrow

        if next_update:
            self._unsub_update = event_helper.async_track_point_in_time(
                self.hass, self._update_state, next_update
            )

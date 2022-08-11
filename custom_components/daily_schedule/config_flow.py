"""Config flow for daily schedule integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import ATTR_END, ATTR_SCHEDULE, ATTR_START, DOMAIN
from .schedule import Schedule

ADD_RANGE = "add_range"
RANGE_DELIMITER = " - "

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
        vol.Required(ADD_RANGE, default=True): selector.BooleanSelector(),
    }
)
CONFIG_RANGE = vol.Schema(
    {
        vol.Required(ATTR_START, default="00:00:00"): selector.TimeSelector(),
        vol.Required(ATTR_END, default="00:00:00"): selector.TimeSelector(),
        vol.Required(ADD_RANGE, default=False): selector.BooleanSelector(),
    }
)
OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_START, default="00:00:00"): selector.TimeSelector(),
        vol.Optional(ATTR_END, default="00:00:00"): selector.TimeSelector(),
    }
)


class DailyScheduleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow."""

    def __init__(self):
        """Initialize a new flow."""
        self.options: dict[str, Any] = {ATTR_SCHEDULE: []}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA)

        if user_input.get(ADD_RANGE, False):
            self.options[CONF_NAME] = user_input[CONF_NAME]
            return await self.async_step_range()

        return self.async_create_entry(
            title=user_input[CONF_NAME],
            data={},
            options={ATTR_SCHEDULE: []},
        )

    async def async_step_range(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding a time range."""
        errors: dict[str, str] = {}

        if user_input is not None:

            # Validate the new schedule.
            time_ranges = self.options[ATTR_SCHEDULE].copy()
            time_ranges.append(
                {ATTR_START: user_input[ATTR_START], ATTR_END: user_input[ATTR_END]}
            )
            try:
                schedule = Schedule(time_ranges)
            except vol.Invalid:
                errors["base"] = "invalid_schedule"

            if not errors:
                self.options[ATTR_SCHEDULE] = schedule.to_list()

                if user_input.get(ADD_RANGE, False):
                    return await self.async_step_range()

                return self.async_create_entry(
                    title=self.options[CONF_NAME],
                    data={},
                    options={ATTR_SCHEDULE: self.options[ATTR_SCHEDULE]},
                )

        return self.async_show_form(
            step_id="range", data_schema=CONFIG_RANGE, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any]) -> FlowResult:
        """Handle an options flow."""
        errors: dict[str, str] = {}

        if user_input is not None:

            # Get all ranges except for the ones which were unchecked by the user.
            time_ranges = [
                {
                    ATTR_START: range.split(RANGE_DELIMITER)[0],
                    ATTR_END: range.split(RANGE_DELIMITER)[1],
                }
                for range in user_input.get(ATTR_SCHEDULE, [])
            ]

            # Add the additional range.
            if user_input.get(ADD_RANGE, True):
                time_ranges.append(
                    {
                        ATTR_START: user_input.get(ATTR_START, "00:00:00"),
                        ATTR_END: user_input.get(ATTR_END, "00:00:00"),
                    }
                )

            try:
                schedule = Schedule(time_ranges)
            except vol.Invalid:
                errors["base"] = "invalid_schedule"

            if not errors:
                return self.async_create_entry(
                    title="",
                    data={ATTR_SCHEDULE: schedule.to_list()},
                )

        ranges = [
            f"{range[ATTR_START]}{RANGE_DELIMITER}{range[ATTR_END]}"
            for range in self.config_entry.options.get(ATTR_SCHEDULE, [])
        ]
        if ranges:
            schema = vol.Schema(
                {
                    vol.Required(ATTR_SCHEDULE, default=ranges): cv.multi_select(
                        ranges
                    ),
                    vol.Required(ADD_RANGE, default=False): cv.boolean,
                }
            ).extend(OPTIONS_SCHEMA.schema)
        else:
            schema = OPTIONS_SCHEMA

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)

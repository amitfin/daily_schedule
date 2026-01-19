"""Config flow for daily schedule integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_SCHEDULE, CONF_SKIP_REVERSED, CONF_UTC, DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigFlowResult

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
    }
)


class DailyScheduleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Verify uniqueness of the name (used as the key).
            duplicated = filter(
                lambda entry: entry.title == user_input[CONF_NAME],
                self.hass.config_entries.async_entries(DOMAIN),
            )
            if list(duplicated):
                errors["base"] = "duplicated"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={},
                    options={CONF_SCHEDULE: []},
                )

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
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
        if "config_entry" not in dir(self):
            self.config_entry = config_entry  # type: ignore  # noqa: PGH003

    async def async_step_init(self, user_input: dict[str, Any]) -> ConfigFlowResult:
        """Handle an options flow."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_SCHEDULE: self.config_entry.options.get(CONF_SCHEDULE, []),
                    CONF_UTC: user_input[CONF_UTC],
                    CONF_SKIP_REVERSED: user_input[CONF_SKIP_REVERSED],
                },
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UTC, default=self.config_entry.options.get(CONF_UTC, False)
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_SKIP_REVERSED,
                        default=self.config_entry.options.get(
                            CONF_SKIP_REVERSED, False
                        ),
                    ): selector.BooleanSelector(),
                }
            ),
        )

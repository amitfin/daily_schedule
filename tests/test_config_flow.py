"""Tests for the Daily Schedule config flow."""
from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.daily_schedule.config_flow import (
    ADD_RANGE,
    RANGE_DELIMITER,
)
from custom_components.daily_schedule.const import (
    ATTR_SCHEDULE,
    CONF_FROM,
    CONF_TO,
    DOMAIN,
)


async def test_config_flow_no_schedule(hass: HomeAssistant) -> None:
    """Test the user flow without a schedule."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == SOURCE_USER
    assert "flow_id" in result

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_NAME: "test", ADD_RANGE: False},
    )

    assert result2.get("type") == FlowResultType.CREATE_ENTRY
    assert result2.get("title") == "test"
    assert result2.get("options") == {ATTR_SCHEDULE: []}


async def test_config_flow_with_schedule(hass: HomeAssistant) -> None:
    """Test the user flow with a schedule."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_NAME: "test"},  # Default is to add a time range
    )
    assert result2.get("type") == FlowResultType.FORM
    assert result2.get("step_id") == "time_range"

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_FROM: "15:00:00", CONF_TO: "20:00:00", ADD_RANGE: True},
    )
    assert result3.get("type") == FlowResultType.FORM
    assert result3.get("step_id") == "time_range"

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_FROM: "05:00:00", CONF_TO: "10:00:00"},
    )
    assert result4.get("type") == FlowResultType.CREATE_ENTRY
    assert result4.get("title") == "test"
    assert result4.get("options") == {
        ATTR_SCHEDULE: [
            {CONF_FROM: "05:00:00", CONF_TO: "10:00:00"},
            {CONF_FROM: "15:00:00", CONF_TO: "20:00:00"},
        ]
    }


async def test_config_flow_invalid_schedule(hass: HomeAssistant) -> None:
    """Test the user flow with an invalid schedule."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_NAME: "test"},
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_FROM: "05:00:00", CONF_TO: "10:00:00", ADD_RANGE: True},
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_FROM: "03:00:00", CONF_TO: "06:00:00"},
    )
    assert result2.get("type") == FlowResultType.FORM
    assert result2.get("step_id") == "time_range"
    assert result2.get("errors")["base"] == "invalid_schedule"


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test the options flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="My Test",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_FROM: "01:00:00",
            CONF_TO: "04:00:00",
        },
    )
    assert result2.get("type") == FlowResultType.CREATE_ENTRY
    assert result2.get("data") == {
        ATTR_SCHEDULE: [
            {CONF_FROM: "01:00:00", CONF_TO: "04:00:00"},
        ]
    }


async def test_invalid_options_flow(hass: HomeAssistant) -> None:
    """Test invalid options flow."""
    config_entry = MockConfigEntry(
        options={ATTR_SCHEDULE: [{CONF_FROM: "05:00:00", CONF_TO: "10:00:00"}]},
        domain=DOMAIN,
        title="My Test",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            ATTR_SCHEDULE: [f"05:00:00{RANGE_DELIMITER}10:00:00"],
            ADD_RANGE: True,
            CONF_FROM: "01:00:00",
            CONF_TO: "06:00:00",
        },
    )
    assert result2.get("type") == FlowResultType.FORM
    assert result2.get("errors")["base"] == "invalid_schedule"

"""Tests for the Daily Schedule config flow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.daily_schedule.config_flow import (
    ADD_RANGE,
)
from custom_components.daily_schedule.const import (
    CONF_FROM,
    CONF_SCHEDULE,
    CONF_TO,
    CONF_UTC,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


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
    assert result2.get("options") == {CONF_SCHEDULE: [], CONF_UTC: False}


async def test_config_flow_duplicated(hass: HomeAssistant) -> None:
    """Test the user flow without a duplicated config entry name."""
    name = "My Test"
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title=name,
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_NAME: name, ADD_RANGE: False},
    )
    assert result2.get("type") == FlowResultType.FORM
    assert (result2.get("errors") or {}).get("base") == "duplicated"


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
        CONF_SCHEDULE: [
            {CONF_FROM: "05:00:00", CONF_TO: "10:00:00"},
            {CONF_FROM: "15:00:00", CONF_TO: "20:00:00"},
        ],
        CONF_UTC: False,
    }
    assert await hass.config_entries.async_unload(
        hass.config_entries.async_entries(DOMAIN)[0].entry_id
    )
    await hass.async_block_till_done()


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test the options flow."""
    config_entry = MockConfigEntry(
        options={CONF_SCHEDULE: [{CONF_FROM: "05:00:00", CONF_TO: "10:00:00"}]},
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
            ADD_RANGE: True,
            CONF_FROM: "01:00:00",
            CONF_TO: "04:00:00",
        },
    )
    assert result2.get("type") == FlowResultType.CREATE_ENTRY
    assert result2.get("data") == {
        CONF_SCHEDULE: [
            {CONF_FROM: "01:00:00", CONF_TO: "04:00:00"},
            {CONF_FROM: "05:00:00", CONF_TO: "10:00:00"},
        ],
        CONF_UTC: False,
    }
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()


async def test_utc(hass: HomeAssistant) -> None:
    """Test UTC."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_NAME: "test", ADD_RANGE: False, CONF_UTC: True},
    )
    assert result2.get("type") == FlowResultType.CREATE_ENTRY

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.options[CONF_UTC] is True

    result3 = await hass.config_entries.options.async_init(config_entry.entry_id)
    result4 = await hass.config_entries.options.async_configure(
        result3["flow_id"],
        user_input={
            CONF_UTC: False,
        },
    )
    assert result4.get("type") == FlowResultType.CREATE_ENTRY

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.options[CONF_UTC] is False

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

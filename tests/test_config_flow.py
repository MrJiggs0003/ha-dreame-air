"""Config, reauth and options flows."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.dreame_air.api import AuthFailed, CannotConnect
from custom_components.dreame_air.const import CONF_DID, CONF_MODEL, CONF_OFF_BEHAVIOR, CONF_SCAN_INTERVAL, DOMAIN

from .conftest import DID, FakeCloud, device_record, make_entry

USER_INPUT = {"username": "user@example.com", "password": "secret", "region": "us"}


async def _start(hass: HomeAssistant):
    return await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})


async def test_single_purifier_creates_entry(hass: HomeAssistant, cloud: FakeCloud) -> None:
    cloud.devices = [device_record(), {"did": "999", "model": "dreame.vacuum.r2228o", "customName": "Vacuum"}]
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Bedroom Purifier"
    assert result["data"][CONF_DID] == DID
    assert result["data"][CONF_MODEL] == "dreame.airp.u2513"
    assert result["result"].unique_id == DID


async def test_choose_between_purifiers(hass: HomeAssistant, cloud: FakeCloud) -> None:
    cloud.devices = [device_record(), device_record(model="dreame.airp.u9999", did="555", name="Office")]
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_DID: "555"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Office"


async def test_errors_then_recover(hass: HomeAssistant, cloud: FakeCloud) -> None:
    result = await _start(hass)
    cloud.login_error = AuthFailed("bad")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"base": "invalid_auth"}
    cloud.login_error = CannotConnect("down")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"base": "cannot_connect"}
    cloud.login_error = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_no_purifiers(hass: HomeAssistant, cloud: FakeCloud) -> None:
    cloud.devices = [{"did": "999", "model": "dreame.vacuum.r2228o"}]
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices"


async def test_already_configured_purifier_is_skipped(hass: HomeAssistant, cloud: FakeCloud) -> None:
    make_entry().add_to_hass(hass)
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices"


async def test_reauth_updates_password(hass: HomeAssistant, cloud: FakeCloud) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    cloud.login_error = AuthFailed("bad")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"password": "wrong"})
    assert result["errors"] == {"base": "invalid_auth"}
    cloud.login_error = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"password": "new"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data["password"] == "new"
    await hass.async_block_till_done()


async def test_options_ap10_offers_real_off(hass: HomeAssistant, cloud: FakeCloud) -> None:
    entry = make_entry(model="dreame.airp.u2507")
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert {str(k) for k in result["data_schema"].schema} == {CONF_OFF_BEHAVIOR, CONF_SCAN_INTERVAL}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_OFF_BEHAVIOR: "real", CONF_SCAN_INTERVAL: 60.0}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_OFF_BEHAVIOR: "real", CONF_SCAN_INTERVAL: 60}


async def test_options_fp10_has_no_real_off(hass: HomeAssistant, cloud: FakeCloud) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert {str(k) for k in result["data_schema"].schema} == {CONF_SCAN_INTERVAL}
    result = await hass.config_entries.options.async_configure(result["flow_id"], {CONF_SCAN_INTERVAL: 45.0})
    assert entry.options == {CONF_SCAN_INTERVAL: 45}

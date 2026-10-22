"""Setting up entries and controlling the purifier through entities."""

from __future__ import annotations

from homeassistant.components.fan import (
    ATTR_PERCENTAGE,
    ATTR_PRESET_MODE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_PERCENTAGE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.number.const import UNIT_CONVERTERS
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er, issue_registry as ir
import pytest

from custom_components.dreame_air.api import AuthFailed
from custom_components.dreame_air.const import DOMAIN

from .conftest import FakeCloud, make_entry

FAN = "fan.bedroom_purifier"


async def _setup(hass: HomeAssistant, **kwargs) -> object:
    entry = make_entry(**kwargs)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_fp10_entities(hass: HomeAssistant, cloud: FakeCloud, entity_registry: er.EntityRegistry) -> None:
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.LOADED
    state = hass.states.get(FAN)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_PRESET_MODE] == "smart"
    assert state.attributes[ATTR_PERCENTAGE] == 50
    assert hass.states.get("sensor.bedroom_purifier_pm2_5").state == "8"
    assert hass.states.get("sensor.bedroom_purifier_tvoc").state == "14"
    assert hass.states.get("sensor.bedroom_purifier_temperature").state == "22"
    assert hass.states.get("sensor.bedroom_purifier_humidity").state == "54"
    assert hass.states.get("sensor.bedroom_purifier_air_quality").state == "excellent"
    assert hass.states.get("sensor.bedroom_purifier_hair_collection_box").state == "100"
    assert hass.states.get("sensor.bedroom_purifier_filter_life").state == "98"
    assert hass.states.get("binary_sensor.bedroom_purifier_filter_replacement_needed").state == STATE_OFF
    assert hass.states.get("light.bedroom_purifier_display").state == STATE_ON
    assert hass.states.get("switch.bedroom_purifier_key_beep").state == STATE_ON
    assert hass.states.get("number.bedroom_purifier_off_timer").state == "0"
    assert hass.states.get("button.bedroom_purifier_reset_filter") is not None
    # The FP10 reports "" for child lock, so it isn't created.
    assert hass.states.get("switch.bedroom_purifier_child_lock") is None
    # Not controllable through the fan, so no duplicate sensors for these.
    assert hass.states.get("sensor.bedroom_purifier_mode") is None


async def test_fan_soft_off_and_on(hass: HomeAssistant, cloud: FakeCloud) -> None:
    await _setup(hass)
    cloud.calls.clear()
    await hass.services.async_call(FAN_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: FAN}, blocking=True)
    assert cloud.writes == [("set", 2, 4, 1), ("set", 2, 3, 2)]
    assert hass.states.get(FAN).state == STATE_OFF
    cloud.calls.clear()
    await hass.services.async_call(FAN_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: FAN}, blocking=True)
    assert cloud.writes == [("set", 2, 3, 0)]
    assert hass.states.get(FAN).state == STATE_ON


async def test_fp10_real_off_option_still_soft(hass: HomeAssistant, cloud: FakeCloud) -> None:
    await _setup(hass, options={"off_behavior": "real"})
    cloud.calls.clear()
    await hass.services.async_call(FAN_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: FAN}, blocking=True)
    assert cloud.writes == [("set", 2, 4, 1), ("set", 2, 3, 2)]
    assert hass.states.get(FAN).state == STATE_OFF


async def test_fp10_in_standby_explains_instead_of_toggling(hass: HomeAssistant, cloud: FakeCloud) -> None:
    cloud.values[(2, 1)] = 2  # someone used the power button
    await _setup(hass)
    assert hass.states.get(FAN).state == STATE_OFF
    cloud.calls.clear()
    with pytest.raises(HomeAssistantError, match="power button"):
        await hass.services.async_call(FAN_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: FAN}, blocking=True)
    assert cloud.writes == []


async def test_fan_speed_and_preset(hass: HomeAssistant, cloud: FakeCloud) -> None:
    await _setup(hass)
    cloud.calls.clear()
    await hass.services.async_call(
        FAN_DOMAIN, SERVICE_SET_PERCENTAGE, {ATTR_ENTITY_ID: FAN, ATTR_PERCENTAGE: 70}, blocking=True
    )
    assert cloud.writes == [("set", 2, 3, 3), ("set", 2, 4, 7)]
    cloud.calls.clear()
    await hass.services.async_call(
        FAN_DOMAIN, SERVICE_SET_PRESET_MODE, {ATTR_ENTITY_ID: FAN, ATTR_PRESET_MODE: "pet"}, blocking=True
    )
    assert cloud.writes == [("set", 2, 3, 4)]
    assert hass.states.get(FAN).attributes[ATTR_PRESET_MODE] == "pet"


async def test_unsupported_model_gets_issue_not_entities(
    hass: HomeAssistant, cloud: FakeCloud, issue_registry: ir.IssueRegistry
) -> None:
    entry = await _setup(hass, model="dreame.airp.u9999")
    assert entry.state is ConfigEntryState.LOADED
    assert not hass.states.async_entity_ids(FAN_DOMAIN)
    assert issue_registry.async_get_issue(DOMAIN, f"unsupported_model_{entry.entry_id}")
    assert not cloud.calls
    await hass.config_entries.async_unload(entry.entry_id)
    assert not issue_registry.async_get_issue(DOMAIN, f"unsupported_model_{entry.entry_id}")


async def test_pm20_is_sensors_only(hass: HomeAssistant, cloud: FakeCloud) -> None:
    cloud.values = {(2, 1): 1, (2, 3): 5, (2, 4): 3, (3, 5): 12, (4, 1): 80}
    await _setup(hass, model="dreame.airp.u2402")
    assert not hass.states.async_entity_ids(FAN_DOMAIN)
    assert not hass.states.async_entity_ids("button")
    assert hass.states.get("sensor.bedroom_purifier_mode").state == "comfort"
    assert hass.states.get("sensor.bedroom_purifier_pm2_5").state == "12"
    assert not cloud.writes


async def test_auth_failure_starts_reauth(hass: HomeAssistant, cloud: FakeCloud) -> None:
    cloud.read_error = AuthFailed("expired")
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert any(f["context"]["source"] == "reauth" for f in flows)


async def test_display_full_brightness_is_fp10_max(hass: HomeAssistant, cloud: FakeCloud) -> None:
    await _setup(hass)
    light = "light.bedroom_purifier_display"
    # Device value 50 of a maximum 80.
    assert hass.states.get(light).attributes["brightness"] == 159
    cloud.calls.clear()
    await hass.services.async_call("light", "turn_on", {ATTR_ENTITY_ID: light, "brightness": 255}, blocking=True)
    assert cloud.writes == [("set", 6, 6, 80)]
    cloud.calls.clear()
    await hass.services.async_call("light", "turn_off", {ATTR_ENTITY_ID: light}, blocking=True)
    assert cloud.writes == [("set", 6, 6, 0)]
    cloud.calls.clear()
    await hass.services.async_call("light", "turn_on", {ATTR_ENTITY_ID: light}, blocking=True)
    assert cloud.writes == [("set", 6, 6, 80)]


async def test_value_missing_from_one_poll_is_kept(hass: HomeAssistant, cloud: FakeCloud) -> None:
    entry = await _setup(hass)
    coordinator = entry.runtime_data
    pm25 = "sensor.bedroom_purifier_pm2_5"
    del cloud.values[(3, 5)]
    for _ in range(2):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert hass.states.get(pm25).state == "8"
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(pm25).state == "unavailable"
    cloud.values[(3, 5)] = 3
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(pm25).state == "3"


@pytest.mark.skipif(
    NumberDeviceClass.DURATION not in UNIT_CONVERTERS,
    reason="This Home Assistant version can't show a number's duration in another unit",
)
async def test_off_timer_in_minutes(hass: HomeAssistant, cloud: FakeCloud, entity_registry: er.EntityRegistry) -> None:
    """Home Assistant converts the timer when someone chooses another unit."""
    cloud.values[(6, 8)] = 2
    await _setup(hass)
    timer = "number.bedroom_purifier_off_timer"
    entity_registry.async_update_entity_options(timer, "number", {"unit_of_measurement": "min"})
    await hass.async_block_till_done()
    state = hass.states.get(timer)
    assert state.attributes["unit_of_measurement"] == "min"
    assert float(state.state) == 120


@pytest.mark.parametrize(("reported", "shown"), [("U2513TEST", "U2513TEST"), ("000000000000000000", None)])
async def test_serial_number(
    hass: HomeAssistant, cloud: FakeCloud, device_registry: dr.DeviceRegistry, reported: str, shown: str | None
) -> None:
    """Some purifiers report a serial of all zeros; that isn't shown."""
    cloud.values[(1, 5)] = reported
    entry = await _setup(hass)
    [device] = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    assert device.serial_number == shown

"""The device layer refuses anything a profile doesn't allow."""

from __future__ import annotations

import pytest

from custom_components.dreame_air.device import DreameDevice, NotAllowed
from custom_components.dreame_air.profiles import get_profile

from .conftest import DID, FakeCloud


def make(model: str, values: dict | None = None) -> tuple[DreameDevice, FakeCloud]:
    cloud = FakeCloud()
    if values is not None:
        cloud.values = values
    return DreameDevice(cloud, get_profile(model), DID, None), cloud  # type: ignore[arg-type]


async def test_tp20_never_reads_3_10_or_toggles_power() -> None:
    device, cloud = make("dreame.airp.u2630", {(2, 1): 2, (2, 3): 0, (2, 4): 1, (3, 10): 5})
    await device.read_all()
    assert (3, 10) not in cloud.addresses_read
    with pytest.raises(NotAllowed):
        await device.run("toggle_power")
    with pytest.raises(NotAllowed):
        await device.turn_on({"power": 2}, None)
    assert not cloud.writes


async def test_tp20_off_is_always_soft() -> None:
    device, cloud = make("dreame.airp.u2630")
    await device.turn_off({"power": 1, "mode": 0}, real=True)
    assert cloud.writes == [("set", 2, 3, 2)]


async def test_pm20_refuses_every_write() -> None:
    device, cloud = make("dreame.airp.u2402", {(2, 1): 1, (2, 5): -1, (2, 6): -1})
    await device.read_all()
    assert not {(2, 5), (2, 6)} & cloud.addresses_read
    with pytest.raises(NotAllowed):
        await device.write("mode", 0)
    with pytest.raises(NotAllowed):
        await device.write("fan_speed", 1)
    assert not cloud.writes


async def test_disallowed_values_and_unknown_keys() -> None:
    device, cloud = make("dreame.airp.u2513")
    with pytest.raises(NotAllowed):
        await device.write("fan_speed", 11)
    with pytest.raises(NotAllowed):
        await device.write("mode", 1)  # Strong: an AP10 mode, not an FP10 one
    with pytest.raises(NotAllowed):
        await device.write("pm25", 0)  # read-only
    with pytest.raises(NotAllowed):
        await device.write("heater", 1)  # not in the profile
    with pytest.raises(NotAllowed):
        await device.run("reset_carbon_filter")
    assert not cloud.writes


async def test_fp10_soft_off_writes_speed_then_sleep() -> None:
    device, cloud = make("dreame.airp.u2513")
    written = await device.turn_off({"power": 1, "mode": 0, "fan_speed": 5}, real=False)
    assert cloud.writes == [("set", 2, 4, 1), ("set", 2, 3, 2)]
    assert device.is_soft_off({"power": 1, **written})


async def test_fp10_never_toggles_power() -> None:
    """Toggling an FP10 on from standby knocked it off the cloud, so 2/3 is never sent."""
    device, cloud = make("dreame.airp.u2513")
    with pytest.raises(NotAllowed):
        await device.run("toggle_power")
    # Real off falls back to soft off.
    await device.turn_off({"power": 1, "mode": 0}, real=True)
    assert cloud.writes == [("set", 2, 4, 1), ("set", 2, 3, 2)]
    cloud.calls.clear()
    with pytest.raises(NotAllowed, match="standby"):
        await device.turn_on({"power": 2, "mode": 0}, None)
    assert cloud.writes == []


async def test_ap10_real_off_and_on_toggle_once() -> None:
    device, cloud = make("dreame.airp.u2507")
    await device.turn_off({"power": 1}, real=True)
    assert cloud.writes == [("action", 2, 3)]
    cloud.calls.clear()
    await device.turn_off({"power": 2}, real=True)
    assert cloud.writes == []
    written = await device.turn_on({"power": 2, "mode": 2}, None)
    assert cloud.writes == [("action", 2, 3), ("set", 2, 3, 0)]
    assert written == {"power": 1, "mode": 0}


async def test_fp10_turn_on_from_soft_off_restores_mode() -> None:
    device, cloud = make("dreame.airp.u2513")
    await device.turn_on({"power": 1, "mode": 2, "fan_speed": 1}, None)
    assert cloud.writes == [("set", 2, 3, 0)]


async def test_set_speed_switches_to_manual_mode() -> None:
    device, cloud = make("dreame.airp.u2513")
    await device.set_speed({"power": 1, "mode": 0}, 7)
    assert cloud.writes == [("set", 2, 3, 3), ("set", 2, 4, 7)]


async def test_scaled_values() -> None:
    device, _ = make("dreame.airp.cvf24a", {(2, 1): 1, (3, 7): 25})
    values = await device.read_all()
    assert values["hcho"] == 0.025

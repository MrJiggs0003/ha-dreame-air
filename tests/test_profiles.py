"""Every profile is internally consistent, and the known hazards are blocked."""

from __future__ import annotations

import pytest

from custom_components.dreame_air.profiles import Profile, Status, all_profiles, get_profile, speeds

PROFILES = all_profiles()


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.name)
def test_profile_is_consistent(profile: Profile) -> None:
    keys = [p.key for p in profile.props]
    assert len(keys) == len(set(keys)), "duplicate property keys"
    addresses = [p.address for p in profile.props]
    assert len(addresses) == len(set(addresses)), "duplicate property addresses"
    for prop in profile.props:
        if prop.writable:
            assert prop.values, f"{prop.key} is writable with no allowed values"
    if profile.power_action:
        action = profile.action(profile.power_action)
        assert action is not None
        assert action.address not in profile.unsafe_actions
    for action in profile.actions:
        assert action.address not in profile.unsafe_actions, f"{action.key} is declared and unsafe"
    if profile.has_fan:
        assert set(profile.prop("mode").values) == set(profile.modes)
        assert set(profile.prop("fan_speed").values) == speeds(profile.speed_count)
        assert profile.manual_mode in profile.modes
        assert profile.on_mode in profile.modes
        for key, value in profile.soft_off:
            prop = profile.prop(key)
            assert prop is not None and prop.writable and value in prop.values


def test_models_are_unique() -> None:
    models = [p.model for p in PROFILES]
    assert len(models) == len(set(models))


def test_unknown_model_has_no_profile() -> None:
    assert get_profile("dreame.airp.u9999") is None


def test_tp20_hazards_blocked() -> None:
    tp20 = get_profile("dreame.airp.u2630")
    assert tp20.power_action is None
    assert (2, 3) in tp20.unsafe_actions
    assert all(a.address != (2, 3) for a in tp20.actions)
    assert (3, 10) not in {p.address for p in tp20.readable}


def test_fp10_power_toggle_blocked() -> None:
    fp10 = get_profile("dreame.airp.u2513")
    assert fp10.status is Status.VERIFIED
    assert fp10.power_action is None
    assert (2, 3) in fp10.unsafe_actions
    assert all(a.address != (2, 3) for a in fp10.actions)
    assert (6, 2) not in {p.address for p in fp10.readable}


def test_pm20_is_read_only_and_heater_untouched() -> None:
    pm20 = get_profile("dreame.airp.u2402")
    assert pm20.status is Status.READ_ONLY
    assert not pm20.controllable
    assert not pm20.has_fan
    assert not pm20.actions
    assert not any(p.writable for p in pm20.props)
    readable = {p.address for p in pm20.readable}
    assert (2, 5) not in readable and (2, 6) not in readable

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


def _values(values: frozenset[int]) -> str:
    low, high = min(values), max(values)
    if values == frozenset(range(low, high + 1)) and high - low > 1:
        return f"{low}..{high}"
    return ",".join(str(v) for v in sorted(values))


def _surface(profile: Profile) -> dict:
    return {
        "status": profile.status.value,
        "writes": {p.key: (p.address, _values(p.values)) for p in profile.props if p.writable},
        "actions": {a.key: a.address for a in profile.actions},
        "power_action": profile.power_action,
        "soft_off": profile.soft_off,
        "unsafe_reads": sorted(profile.unsafe_reads),
        "unsafe_actions": sorted(profile.unsafe_actions),
    }


# Everything each model may be sent, spelled out. A change here is a change to
# what reaches real purifiers, so it should be deliberate and visible in review.
SURFACE = {
    "dreame.airp.u2513": {
        "status": "verified",
        "writes": {
            "mode": ((2, 3), "0,2,3,4"),
            "fan_speed": ((2, 4), "1..10"),
            "child_lock": ((6, 5), "0,1"),
            "display_brightness": ((6, 6), "0..80"),
            "off_timer": ((6, 8), "0..12"),
            "display_breathing": ((6, 12), "0,1"),
            "key_tone": ((6, 17), "0,1"),
        },
        "actions": {"reset_filter": (4, 1)},
        "power_action": None,
        "soft_off": (("fan_speed", 1), ("mode", 2)),
        "unsafe_reads": [(6, 2)],
        "unsafe_actions": [(2, 3)],
    },
    "dreame.airp.u2507": {
        "status": "community",
        "writes": {
            "mode": ((2, 3), "0..4"),
            "fan_speed": ((2, 4), "1..5"),
            "light_color": ((2, 6), "-1..2"),
            "key_tone": ((2, 7), "0,1"),
            "child_lock": ((6, 5), "0,1"),
            "off_timer": ((6, 8), "0..12"),
        },
        "actions": {"toggle_power": (2, 3), "reset_filter": (4, 1)},
        "power_action": "toggle_power",
        "soft_off": (("fan_speed", 1), ("mode", 2)),
        "unsafe_reads": [],
        "unsafe_actions": [],
    },
    "dreame.airp.cvf24a": {
        "status": "community",
        "writes": {
            "mode": ((2, 3), "0,2,3,4"),
            "fan_speed": ((2, 4), "1..10"),
            "off_timer": ((6, 8), "0..24"),
        },
        "actions": {"toggle_power": (2, 3), "reset_filter": (4, 1), "reset_carbon_filter": (5, 1)},
        "power_action": "toggle_power",
        "soft_off": (("mode", 3), ("fan_speed", 1)),
        "unsafe_reads": [],
        "unsafe_actions": [],
    },
    "dreame.airp.u2630": {
        "status": "community",
        "writes": {
            "mode": ((2, 3), "0,2,3"),
            "fan_speed": ((2, 4), "1..3"),
            "off_timer": ((6, 8), "0..12"),
            "child_lock": ((6, 10), "0,1"),
        },
        "actions": {"reset_filter": (4, 1)},
        "power_action": None,
        "soft_off": (("mode", 2),),
        "unsafe_reads": [(3, 10)],
        "unsafe_actions": [(2, 3)],
    },
    "dreame.airp.u2402": {
        "status": "read_only",
        "writes": {},
        "actions": {},
        "power_action": None,
        "soft_off": (),
        "unsafe_reads": [(2, 5), (2, 6)],
        "unsafe_actions": [],
    },
}


def test_surface_matches_the_reviewed_table() -> None:
    assert {p.model: _surface(p) for p in PROFILES} == SURFACE

"""Dreame TP20 (dreame.airp.u2630).

Property map reported by CyberoniOntoni/dreame-TP20-integration. Not tested by
this project.

Two hazards reported there, both blocked here:
- Reading 3/10 makes the TP20 stop responding and reboot.
- Action 2/3, the power toggle on the FP10 and PM10, leaves the TP20 dead until
  its power button is pressed, and it may not reconnect to Wi-Fi.
Its power property is read-only, so the TP20 has no remote power control.
"""

from . import ON_OFF, Action, Profile, Prop, Status, speeds, value_range

AI, SLEEP, CUSTOM = 0, 2, 3

PROFILE = Profile(
    model="dreame.airp.u2630",
    name="TP20",
    status=Status.COMMUNITY,
    props=(
        Prop("power", 2, 1),
        Prop("mode", 2, 3, values=frozenset({AI, SLEEP, CUSTOM})),
        Prop("fan_speed", 2, 4, values=speeds(3)),
        Prop(
            "air_quality_level",
            3,
            4,
            options={1: "excellent", 2: "good", 3: "moderate", 4: "poor", 5: "bad"},
        ),
        Prop("pm25", 3, 5),
        Prop("filter_life", 4, 1),
        Prop("filter_days_left", 4, 2),
        Prop("off_timer", 6, 8, values=value_range(0, 12)),
        Prop("child_lock", 6, 10, values=ON_OFF),
    ),
    actions=(Action("reset_filter", 4, 1),),
    power_action=None,
    modes={AI: "smart", SLEEP: "sleep", CUSTOM: "customize"},
    manual_mode=CUSTOM,
    on_mode=AI,
    speed_count=3,
    soft_off=(("mode", SLEEP),),
    unsafe_reads=frozenset({(3, 10)}),
    unsafe_actions=frozenset({(2, 3)}),
)

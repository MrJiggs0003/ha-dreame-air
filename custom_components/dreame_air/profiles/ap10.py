"""Dreame AP10 (dreame.airp.u2507).

Property map reported by CodyJon/dreame-ap10-integration (live-tested there in
2025). Not tested by this project.
"""

from . import ON_OFF, Action, Profile, Prop, Status, speeds, value_range

AI, STRONG, SLEEP, CUSTOM, PET = 0, 1, 2, 3, 4

PROFILE = Profile(
    model="dreame.airp.u2507",
    name="AP10",
    status=Status.COMMUNITY,
    props=(
        Prop("power", 2, 1),  # 1 on, 2 standby
        Prop("mode", 2, 3, values=frozenset({AI, STRONG, SLEEP, CUSTOM, PET})),
        Prop("fan_speed", 2, 4, values=speeds(5)),
        Prop(
            "light_color",
            2,
            6,
            values=frozenset({-1, 0, 1, 2}),
            options={-1: "off", 0: "blue", 1: "orange", 2: "green"},
        ),
        Prop("key_tone", 2, 7, values=ON_OFF),
        Prop("air_quality_level", 3, 4),
        Prop("pm25", 3, 5),
        Prop("filter_life", 4, 1),
        Prop("filter_days_left", 4, 2),
        Prop("filter_hours_used", 4, 3),
        Prop("child_lock", 6, 5, values=ON_OFF),
        Prop("off_timer", 6, 8, values=value_range(0, 12)),
    ),
    actions=(
        Action("toggle_power", 2, 3),
        Action("reset_filter", 4, 1),
    ),
    power_action="toggle_power",
    modes={AI: "smart", STRONG: "strong", SLEEP: "sleep", CUSTOM: "customize", PET: "pet"},
    manual_mode=CUSTOM,
    on_mode=AI,
    speed_count=5,
    soft_off=(("fan_speed", 1), ("mode", SLEEP)),
)

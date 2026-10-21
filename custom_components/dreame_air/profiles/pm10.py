"""Dreame PM10 (dreame.airp.cvf24a).

Property map reported by CyberoniOntoni/dreame-TP20-integration, where the PM10
is the upstream author's own unit. Not tested by this project.
"""

from . import Action, Profile, Prop, Status, speeds, value_range

AUTO, COMFORT, CUSTOM, PET = 0, 2, 3, 4

PROFILE = Profile(
    model="dreame.airp.cvf24a",
    name="PM10",
    status=Status.COMMUNITY,
    props=(
        Prop("power", 2, 1),
        Prop("mode", 2, 3, values=frozenset({AUTO, COMFORT, CUSTOM, PET})),
        Prop("fan_speed", 2, 4, values=speeds(10)),
        Prop("humidity", 3, 2),
        Prop("temperature", 3, 3),
        Prop("air_quality_level", 3, 4),
        Prop("pm25", 3, 5),
        Prop("pm10", 3, 6),
        Prop("hcho", 3, 7, scale=0.001),  # reported in µg/m³, shown in mg/m³
        Prop("tvoc", 3, 8),
        Prop("pm1", 3, 10),
        Prop("filter_life", 4, 1),
        Prop("filter_hours_used", 4, 3),
        Prop("carbon_filter_life", 5, 1),
        Prop("carbon_filter_hours_used", 5, 3),
        Prop("off_timer", 6, 8, values=value_range(0, 24)),
    ),
    actions=(
        Action("toggle_power", 2, 3),
        Action("reset_filter", 4, 1),
        Action("reset_carbon_filter", 5, 1),
    ),
    power_action="toggle_power",
    modes={AUTO: "smart", COMFORT: "comfort", CUSTOM: "customize", PET: "pet"},
    manual_mode=CUSTOM,
    on_mode=AUTO,
    speed_count=10,
    soft_off=(("mode", CUSTOM), ("fan_speed", 1)),
)

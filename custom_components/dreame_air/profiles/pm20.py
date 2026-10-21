"""Dreame AirPursue PM20 (dreame.airp.u2402).

Property map from osmnnl/dreame-pm20 (MIT), confirmed there by a read-only sweep
of a real PM20. That project never wrote to the device, so this profile is
read-only too. The PM20 also heats (2/5 and 2/6); those addresses are never read
or written here.
"""

from . import Profile, Prop, Status

PROFILE = Profile(
    model="dreame.airp.u2402",
    name="AirPursue PM20",
    status=Status.READ_ONLY,
    props=(
        Prop("firmware", 1, 4),
        Prop("power", 2, 1),
        Prop("mode", 2, 3, options={0: "smart", 3: "customize", 4: "pet", 5: "comfort"}),
        Prop("fan_speed", 2, 4),
        Prop("humidity", 3, 2),
        Prop("temperature", 3, 3),
        Prop(
            "air_quality_level",
            3,
            4,
            options={1: "excellent", 2: "good", 3: "moderate", 4: "poor"},
        ),
        Prop("pm25", 3, 5),
        Prop("pm10", 3, 6),
        Prop("tvoc", 3, 8),
        Prop("pm1", 3, 10),
        Prop("filter_life", 4, 1),
        Prop("filter_days_left", 4, 2),
        Prop("carbon_filter_life", 4, 3),
        Prop("carbon_filter_days_left", 4, 4),
        Prop("off_timer", 6, 8),
    ),
    unsafe_reads=frozenset({(2, 5), (2, 6)}),
)

"""Dreame FP10 (dreame.airp.u2513).

Property map from yarimati/ha-dreame-fp10 (MIT), confirmed there by a live
read-only sweep of a real FP10, with the sensors corrected here: on a real FP10,
3/5 matched the app's PM2.5 and 3/9 its TVOC (µg/m³), and 4/5 its hair
collection box. 3/12 isn't PM2.5: it's the number on the purifier's own display,
with 3/13 naming it ("PM2.5-1", "TVOC-49"). 3/6, 3/11 and 4/6 match nothing in
the app, so they aren't read. 3/2 humidity, 3/3 temperature (°C) and 3/4 air
quality matched the app (54 %, 22 °C = 71.6 °F, 1 = "Excellent"); they reported
nothing for the first hour after the purifier was re-paired.

Reading 6/2 (the app's schedules) times out every time, which makes the cloud
report the purifier offline for that request, so it's never read.

Verified on a real FP10 (firmware 2072, 2026-10-21): every preset, speeds,
soft off and back on, display brightness and breathing, key beep and off
timer, each confirmed both by the cloud and by watching the purifier. Not
exercised: filter reset (it would have cleared a real filter count).

No remote power control. Power goes through the toggle action 2/3 (writing 2/1
times out). Toggling off works, but toggling back on from standby switched the
purifier on and then knocked it off the cloud: neither Home Assistant nor the
Dreamehome app could control it until it was reset and re-paired in the app,
which also wiped its settings and filter counter. So 2/3 is blocked, and "off"
is always soft off.
"""

from . import ON_OFF, Action, Profile, Prop, Status, speeds, value_range

SMART, SLEEP, CUSTOMIZE, PET = 0, 2, 3, 4

PROFILE = Profile(
    model="dreame.airp.u2513",
    name="FP10",
    status=Status.VERIFIED,
    props=(
        Prop("firmware", 1, 4),
        Prop("serial", 1, 5),
        Prop("power", 2, 1),  # 1 on, 2 standby
        Prop("mode", 2, 3, values=frozenset({SMART, SLEEP, CUSTOMIZE, PET})),
        Prop("fan_speed", 2, 4, values=speeds(10)),
        Prop("humidity", 3, 2),
        Prop("temperature", 3, 3),
        # Only 1 = Excellent is confirmed; the rest follow the TP20's five levels.
        Prop(
            "air_quality_level",
            3,
            4,
            options={1: "excellent", 2: "good", 3: "moderate", 4: "poor", 5: "bad"},
        ),
        Prop("pm25", 3, 5),
        Prop("tvoc", 3, 9),
        Prop("filter_life", 4, 1),
        Prop("filter_days_left", 4, 2),
        Prop("filter_hours_used", 4, 3),
        Prop("hair_box_life", 4, 5),
        # Reads "" on the units mapped so far, so it's only shown if it reports a value.
        Prop("child_lock", 6, 5, values=ON_OFF, needs_value=True),
        # Caps at 80: a write of 100 read back as 80 on a real FP10 (fw 2072).
        Prop("display_brightness", 6, 6, values=value_range(0, 80)),
        Prop("off_timer", 6, 8, values=value_range(0, 12)),
        Prop("display_breathing", 6, 12, values=ON_OFF),
        Prop("key_tone", 6, 17, values=ON_OFF),
    ),
    actions=(Action("reset_filter", 4, 1),),
    power_action=None,
    modes={SMART: "smart", SLEEP: "sleep", CUSTOMIZE: "customize", PET: "pet"},
    manual_mode=CUSTOMIZE,
    on_mode=SMART,
    speed_count=10,
    # Speed first: a speed write can switch the FP10 to Customize, so Sleep goes last.
    soft_off=(("fan_speed", 1), ("mode", SLEEP)),
    unsafe_reads=frozenset({(6, 2)}),
    unsafe_actions=frozenset({(2, 3)}),
)

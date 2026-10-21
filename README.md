# Dreame Air

A Home Assistant integration for Dreame air purifiers that use the **Dreamehome** app.

It works through Dreame's cloud, the same way the app does, so it needs an internet connection. These purifiers don't offer local control.

> Unofficial. Not affiliated with or endorsed by Dreame.

## Supported models

| Model | Model ID | Status | What you get |
|---|---|---|---|
| FP10 | `dreame.airp.u2513` | **Verified** | Fan (on/off, speed, Smart/Sleep/Customize/Pet), PM2.5, TVOC, temperature, humidity, air quality, filter life and days left, hair collection box, filter reset, display brightness and breathing, key beep, off timer, child lock if your unit reports it. Off is always soft off (see below) |
| AP10 | `dreame.airp.u2507` | Untested | Fan (on/off, 5 speeds, 5 modes), PM2.5, air quality, filter, light color, key beep, child lock, off timer |
| PM10 | `dreame.airp.cvf24a` | Untested | Fan (on/off, speed, modes), PM2.5, PM10, PM1, TVOC, formaldehyde, temperature, humidity, HEPA and carbon filters, off timer |
| TP20 | `dreame.airp.u2630` | Untested | Speed, modes, PM2.5, air quality, filter, child lock, off timer. **No power control** (see below) |
| AirPursue PM20 | `dreame.airp.u2402` | Sensors only | PM2.5, PM10, PM1, TVOC, temperature, humidity, air quality, mode, fan speed, filters. **No controls** |

"Untested" profiles come from other owners' published findings and haven't been tried by this project. If you have one, please [report](../../issues) what works and what doesn't.

Other Dreame purifiers can be added (no entities are created for them in the meantime). Dreame robot vacuums aren't covered; use [Tasshack/dreame-vacuum](https://github.com/Tasshack/dreame-vacuum) for those.

## Why some models are limited

Dreame purifiers don't all understand commands the same way, and the wrong one can crash a unit. The power command that works on the FP10 knocks a TP20 offline until someone presses its button, and reading one particular sensor reboots a TP20. So this integration only ever sends a model the reads and commands its profile explicitly allows. Anything else is refused before it leaves Home Assistant.

That's also why unknown models get a notice instead of entities: guessing isn't safe.

## Installation

1. In HACS, open the ⋮ menu → **Custom repositories**, add this repository's URL, and choose **Integration**.
2. Search for **Dreame Air**, download it, and restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration → Dreame Air**.
4. Sign in with your Dreamehome email and password, choose your region, and pick the purifier.

### Signed up with Google or Apple?

Dreame doesn't let other apps use Google or Apple sign-in, so this integration (like every other Dreame integration) needs an email and password. Add a password to your account first:

1. In the Dreamehome app, open **Profile → Settings → Account and Security**.
2. Set a password.
3. In Home Assistant, sign in with your account's email and that password.

Your Google or Apple sign-in keeps working in the app. Phone-number-only accounts may not work; link an email in the same menu if yours has none. After several failed attempts, Dreame may block sign-in for about an hour.

Add each purifier separately. Your login is stored by Home Assistant like any other integration's; only a salted hash of the password is sent to Dreame, the same as the app.

## "Off" and soft off

Turning the purifier **off** in Home Assistant switches it to its quietest setting (for the FP10, Sleep mode at speed 1), and Home Assistant shows it as off. It stays connected and turns back on instantly.

Fully powering a purifier down from Home Assistant is risky. On a real FP10, powering it back on remotely switched it on and then knocked it off Dreame's cloud: neither Home Assistant nor the Dreamehome app could control it until it was reset and re-paired in the app, which also wiped its settings and filter counter. So:

- **FP10 and TP20:** always soft off. Home Assistant never sends their power command. If the purifier was switched off with its own button, turn it on with the button or the Dreamehome app; Home Assistant explains this instead of trying.
- **AP10 and PM10:** soft off by default. The **Configure** options offer **Real off**, based on other owners' reports, but given the FP10 result, use it with care.

## Options

- **What "off" does:** soft off (default) or real off, on models where real off is offered.
- **Update interval:** 15 to 300 seconds (default 30). Changes you make take effect immediately in Home Assistant; the cloud catches up within a few seconds.

## Adding a model

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: each model is one small profile file, mapped carefully on a real unit.

## Credits

- [yarimati/ha-dreame-fp10](https://github.com/yarimati/ha-dreame-fp10) (MIT): the Dreame cloud protocol and the FP10 property map.
- [CodyJon/dreame-ap10-integration](https://github.com/CodyJon/dreame-ap10-integration): the AP10 property map and the original protocol reverse-engineering.
- [CyberoniOntoni/dreame-TP20-integration](https://github.com/CyberoniOntoni/dreame-TP20-integration): the PM10 and TP20 property maps, and the TP20 hazards.
- [osmnnl/dreame-pm20](https://github.com/osmnnl/dreame-pm20) (MIT): the PM20 property map.

No code was copied from projects without a license; only the factual property and command numbers were used, with thanks.

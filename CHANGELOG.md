# Changelog

## Unreleased

- README: Dreame Air is now in the default HACS store, so the install steps no longer add a custom repository.

## 0.1.6

No changes to how the integration works.

- README: a screenshot of the fan control, and links that also work on the HACS page.

## 0.1.5

- The device page no longer shows a serial number of all zeros, which some purifiers (the FP10) report instead of a real one.
- README: a screenshot of the FP10 in Home Assistant.

## 0.1.4

- Requires Home Assistant 2025.4 or later. Earlier versions were listed as supported but couldn't load the integration (2025.2), or can't be tested (2025.3).
- The tests now also run against Home Assistant 2025.4, and weekly against the latest release.

## 0.1.3

- The integration has its own icon, shown in Home Assistant 2026.3 and later.

## 0.1.2

- Fixed: the off timer now shows the right value when you display it in another unit, such as minutes. It showed the number of hours with the new unit.
- For developers: a dev container, `scripts/` for setup, tests, linting and a test Home Assistant, type checking in CI, and automated releases from version tags. See CONTRIBUTING.md.

## 0.1.1

No changes to how the integration works.

- README: an "Open in HACS" button, a list of the entities you get, troubleshooting and example automations.
- Issue forms for bug reports and new models, a pull request checklist and a security policy.
- Dependabot keeps the GitHub Actions up to date.

## 0.1.0

First release.

- Cloud connection to Dreamehome purifiers, with sign-in, reauthentication and options.
- FP10 (verified on a real unit): fan with speeds and presets, PM2.5, TVOC, temperature, humidity, air quality, filter and hair collection box, display, key beep, off timer, child lock.
- AP10, PM10 and TP20 (untested) and AirPursue PM20 (sensors only), from other owners' published findings.
- Per-model allowlists: a purifier is only ever sent the reads and commands its profile declares.
- Soft off by default, since a fully powered-off FP10 can't be switched back on remotely.

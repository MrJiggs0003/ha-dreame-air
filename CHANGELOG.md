# Changelog

## Unreleased

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

# Adding or fixing a model

Each purifier model is one file in `custom_components/dreame_air/profiles/`. A profile is plain data: which properties exist, which values may be written, which actions may run, and which ones are unsafe. The device layer refuses everything else, so a mistake in one profile can't affect another model.

## Mapping a new model safely

Reading the wrong property can crash some models (the TP20 reboots when 3/10 is read). So:

1. Start from the model's ID: open this integration's diagnostics for the unsupported entry, or use `tools/probe.py --list`.
2. Use `tools/probe.py` to read properties **one at a time**, starting with the common ones (2/1 power, 2/3 mode, 2/4 speed, 4/1 filter life). It only reads, never writes, and asks before each step. If the purifier stops responding, note the last address and add it to `unsafe_reads`.
   Some reads just time out, and the cloud then calls the purifier offline for that request: on the FP10, 6/2 (the app's schedules) always does. A purifier can also report nothing for a sensor for a while after a restart or re-pair, so read twice before deciding an address is empty.
3. Change one setting in the Dreamehome app, read again, and note what moved. Repeat for each feature.
4. Don't write anything until you know what it does. Add a write to the profile only after confirming it on your unit, with the exact allowed values.
5. Note in the profile's docstring how each part was confirmed.

## Profile checklist

- `status`: `community` until it's been tested end to end on a real unit, or `read_only` if nothing has been written.
- `power_action`: the action that toggles power, or `None` if there's no confirmed safe one.
- `soft_off`: writes, in order, that put it in its quietest state.
- `unsafe_reads` / `unsafe_actions`: anything known to crash it.
- Add the profile to `all_profiles()` in `profiles/__init__.py`.
- Add a test in `tests/test_device.py` for anything unusual, especially hazards.

## Development

The easiest way is the dev container: open the repository in VS Code with the Dev Containers extension (or in GitHub Codespaces) and choose **Reopen in Container**. It sets everything up.

To set up by hand instead, you need Python 3.14 and Linux or macOS:

```
scripts/setup     # creates .venv with Home Assistant, pytest, ruff and mypy
```

Then:

| Command | What it does |
|---|---|
| `scripts/test` | Runs the tests. Extra arguments go to pytest, for example `scripts/test -k fan` |
| `scripts/lint` | Formats, lints and type-checks. `--check` changes nothing, as in CI |
| `scripts/develop` | Starts a test Home Assistant with this integration at http://localhost:8123. Its data stays in `config/` |

The tests use a fake Dreame cloud (`tests/conftest.py`) that records every command, so they never touch a real purifier. To test against your own purifier, add it in the `scripts/develop` instance, which is separate from your real Home Assistant.

## Releasing

For maintainers:

1. Move the **Unreleased** notes in CHANGELOG.md under a new `## X.Y.Z` heading.
2. Set the same version in `custom_components/dreame_air/manifest.json` and `pyproject.toml`. `scripts/check-version` confirms they all agree.
3. Commit, push, and wait for the checks to pass.
4. Tag and push: `git tag vX.Y.Z && git push origin vX.Y.Z`.

The Release workflow runs the tests again, checks that the tag matches the version, and publishes a GitHub release with the changelog section as its notes. HACS then offers the update.

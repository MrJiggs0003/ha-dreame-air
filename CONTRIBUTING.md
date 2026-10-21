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

```
uv venv --python 3.14
uv pip install pytest-homeassistant-custom-component ruff
pytest
ruff check . && ruff format --check .
```

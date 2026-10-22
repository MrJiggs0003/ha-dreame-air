## What this changes

<!-- What and why, in a sentence or two. Link the issue if there is one. -->

## Checklist

- [ ] `pytest` passes
- [ ] `ruff check . && ruff format --check .` passes
- [ ] CHANGELOG.md has an entry under **Unreleased**

### If this adds or changes a model profile

- [ ] Each property and command was confirmed on a real unit, and the profile's docstring says how
- [ ] Writes list their exact allowed values
- [ ] Anything that made the purifier stop responding is in `unsafe_reads` or `unsafe_actions`
- [ ] `status` is right: `verified` only if tested end to end, otherwise `community` or `read_only`
- [ ] There's a test for anything unusual, especially hazards
- [ ] The README's supported models table is updated

## Tested on

<!-- Model, firmware version and Home Assistant version, or "tests only". -->

# MO2 Modlist Manager — Base

Part 1 establishes the application foundation. It deliberately does **not**
read or write MO2 `modlist.txt` files yet.

## Included

- Versioned JSON settings with configurable game engines and MO2 instances.
- Engine registry with active/retired engine support.
- Dynamic compatibility mapping (`True`, `False`, or `None` for unknown).
- Ordered modlist models with explicit mod/separator types.
- Validation for settings and in-memory master lists.
- A small CLI to validate and display the configuration.

## Requirements

Python 3.10 or newer. No third-party runtime dependencies.

## Run from the project directory

```bash
python -m mo2_modlist_manager
```

Or install in editable mode:

```bash
python -m pip install -e .
mo2-modlist-manager
```

The first run creates `settings.json` in the current working directory if it
does not exist. The generated configuration is intentionally small and can
be edited by hand.

## Compatibility values

- `true`: confirmed compatible
- `false`: confirmed incompatible
- `null`: unknown / not evaluated

An engine removed from the active list should be marked `retired`, not deleted.
Its compatibility data remains attached to each entry.

## Deliberate boundaries for Part 1

Not implemented yet: MO2 parsing/export, CSV persistence, merging, partial-list
boundary detection, patches, backups, history, and graphical UI. Those belong
to later parts. The model already exposes dynamic CSV column names to make the
next stage straightforward.

Continue reading in [PART2-BACKEND](PART2-BACKEND.md).

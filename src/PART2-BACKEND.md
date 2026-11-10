# MO2 Modlist Manager — Part 2 (Backend)

The application maintains runtime compatibility data and synchronizes lists.

## Backend modules

- `parser.py`: parses MO2 `modlist.txt` (`+` enabled, `-` disabled; `separator_` prefix).
- `exporter.py`: serializes the ordered list back to MO2 text.
- `csv_store.py`: reads/writes dynamic master CSV.
- `merge.py`: creates a non-destructive merge preview.
- `workflow.py`: persists review markers outside the CSV.
- `history.py`: immutable imports, patches, revision hashes and snapshots.
- `repository.py`: guarded commit with backups and rollback.
- `models.py`: mod/separator records and dynamic compatibility mapping.

## CSV structure

Example (the content is not fix - engine numbers can vary).
Registration of custom mod content - third-party skse plugins.

```csv
Name,Type,HasDLL,Active,skyrim-1.5.97,1.5.97_active,skyrim-1.6.1170,1.6.1170_active,
```

- `Active`: imported MO2 mod activation state (`1`/`0`).
- `HasDLL`: `1` = SKSE DLL, `0` = no SKSE DLL, empty = not classified yet.
- Engine entries: `1` = compatible, `0` = incompatible, empty = unknown.
- Engine active entries: `1` = active version, `0` = inactive version
  -> only one version can be active at a given time, if compatible
- Separators have blank `HasDLL`, engine and `_active` cells.
- Review status is intentionally stored in `workflow.json`, not CSV.

The legacy CSV schema without `HasDLL` is accepted; missing DLL data becomes
unknown (`None`) and is written with the new column on the next save.

`Active` is only changed internally when it is made active/inactive by a 
different modlist.txt source (when HasDLL=true). This is the combination
table for clarity:

|HasDll | Engine | Active  | Active for other Engines
|-------|--------|---------|-------------------------
| True  |    1   |  0      | -> acts like a global disable (other engines are set to 0)
| True  |    1   |  1      | -> other Engines with "1" are set to Active
| True  |    0   |  0      | -> automatically disabled
| True  |    0   |  1      | -> is automatically disabled
| False |    -   |  1      | -> no automatism
| False |    -   |  0      | -> no automatism

## Review workflow

`ReviewStatus.UNSET` / `ReviewStatus.DONE` tracks whether a maintainer has
completed the compatibility review for an SKSE mod. It is independent of the
compatibility values. `unreviewed_skse_mods()` returns the names to show in a
save warning. Marking a mod reviewed does not assert that all compatibility
values are `True`; the UI use this as model for its own review interaction.

## Merge safety

`preview_merge()` never mutates either input. `SourceScope.ASK` makes no
removal candidates. `PARTIAL` makes no removal candidates. `COMPLETE` can
produce candidates based on matched positional anchors. Trailing disabled
source entries do not extend the inferred boundary; an all-disabled source
has no inferred boundary and needs an explicit override/decision.

The preview lists candidates; removals happen only when their names are passed
in `remove_missing`. The UI must show the effective boundary and warnings.

## History and commit

- Original imports are copied to `momm-data/history/imports/<timestamp>/`.
- Patches are JSON entries that act as operations with expected and resulting master revisions.
- Snapshots are retained according to `keep_snapshots`; this way baseline is preserved.
- Repository commits back up the master CSV and workflow extra data before writing.
- If a commit fails, the previous CSV and workflow metadata are restored.

The repository requires the caller to pass the exact `before` state used to
prepare the operation. A revision check rejects stale commits.

## Part 2 limitations / explicit next refinements

- `_separator` is the parser's separator convention. This has been verified
  with the current stable 2.5.2 release of MO2.
- Source file archiving is provided by `HistoryManager.archive_import`; the
  import orchestration and merge-confirmation UI will be wired in later.
- Export currently preserves activation state; it does not filter mods based
  on compatibility. This prevents accidental activation/deactivation policy
  from being hidden inside serialization. See CSV structure for specific
  cases (export will already get the potentially correct mod informations)
- Full system tests and the use-case-driven acceptance suite belong to Part 4.

Continue reading in [PART3-USERINTERFACE](PART3-USERINTERFACE.md).

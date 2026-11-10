# Extensions for Python app Momm

This part extends on Backups and Partial Mod Lists.
The application becomes an auditable history of modlist states, and 
merging becomes position-aware rather than simply comparing two sets of names.

## 1. Preserving every imported modlist

Fundamental rule: never modify an imported source file.
For each import, preserve:

- Original `modlist.txt`, byte-for-byte if possible.
- A timestamped parsed snapshot.
- The changes made to the master database.

For example:

```
momm-data/
├── master.csv
├── history/
│   ├── 2026-11-08_143500/
│   │   ├── modlist.txt
│   │   ├── source.csv
│   │   └── changes.json
│   └── 2026-11-08_161200/
│       ├── modlist.txt
│       ├── source.csv
│       └── changes.json
└── patches/
    ├── 0001_initial_import.json
    ├── 0002_runtime_compatibility.json
    └── 0003_removed_mods.json
```

Use a timestamp format of `YYYY-MM-DD_HHMMSS` to avoid filename collisions and
make chronological sorting natural.

### Master + patches vs. full snapshots

I prefer your hybrid approach:

- Master CSV: current authoritative state.
- Patches: incremental changes, with enough information to reconstruct history.
- Original modlists: permanent import records.
- Full snapshots: periodic checkpoints, keeping at least the last ten.

One refinement: patches should record operations, not just changed rows.

For example:

```
{
  "operation": "set_compatibility",
  "name": "Example Mod",
  "runtime": "1.7",
  "old": true,
  "new": false
}
```

This makes changes understandable and reversible.
The patch should contain the previous value (Otherwise, reverting a change becomes more complicated)

Important: A patch may be applied only against the expected previous master revision.
This prevents accidentally applying an old patch to an unrelated database state.

## 2. Analysis of the three incomplete-list cases

Introduction of "Effective list boundary".

Distinction is between:

- Physical end of the imported file.
- Last position that provides evidence of a complete modlist.

### a) Simple mods from a specific version

Example: the source is a 1.5.97 installation and contains only its specific SKSE plugins.
Classify those missing entries as potentially removable.
Add a `removable` classification to the merge preview, not to the permanent mod data. 
It's a decision about the current import, not an intrinsic property of a mod.

### b) Partial modlist

Position heuristic:

| Missing entry position             | Treatment         |
| ---------------------------------- | ----------------- |
| Within the effective list boundary | Removal candidate |
| Beyond the effective list boundary | Ignore            |
| Explicitly retained by user        | Keep              |

This is a good conservative approach
Calculate positions relative to the existing list (do not compare unrelated line numbers).
For that, matched entries serve as anchors. Their relative ordering is used to determine
where the imported list ends in the master list.

### c) Partial modlist in disguise

A list can look complete because it contains all its entries, but its trailing entries are disabled.
Trailing disabled entries do not extend the effective list boundary.
For example:

```
+Base
+Framework A
+Framework B
+Main Mod A
+Main Mod B
-Optional Mod A
-Optional Mod B
-Optional Mod C
```

The effective boundary is `Main Mod B`, not `Optional Mod C`.
Consequently, missing entries beyond that boundary should not be treated as removal candidates.

Refinement: 
Only a continuous trailing sequence of disabled entries should be ignored. 
Disabled entries in the middle of the list must remain part of the positional comparison.
-> avoids confusing ordinary disabled mods with an incomplete installation.

## 3. One unavoidable ambiguity

There is a case the heuristic cannot reliably distinguish:

```
+Base
+Framework A
+Main Mod A
-Optional Mod A
-Optional Mod B
```

This could be:

1. An incomplete installation where optional mods were never installed.
2. A complete installation where optional mods are deliberately disabled.

Both produce identical `modlist.txt` data.
This shall not be solved automatically. Instead, show the inferred boundary
in the merge preview and allow the user to override it.
Handle the special case where there are no active entries:
The application requests a boundary decision rather than guess.

## 4. A refinement to the history architecture

Distinguish three kinds of records:

| Record                    | Retention                      |
| ------------------------- | ------------------------------ |
| Original imported modlist | Permanent                      |
| Parsed source snapshot    | Permanent                      |
| Full master snapshot      | Last 10, plus initial baseline |
| Incremental patches       | Permanent                      |

Optionally store a SHA-256 hash of each original file. 
This helps identify duplicate imports and verify that archived files haven't changed.
Important: Zse the original file's modification timestamp as metadata, use the import
timestamp for the archive filename. These represent different things.

## 5. Recommended merge algorithm adjustment

The resulting process should be:

1. Parse the source into ordered entries.
2. Identify active and disabled entries.
3. Determine the effective boundary.
4. Match existing entries using their names and separators.
5. Establish positional anchors between source and master.
6. Identify new entries.
7. Identify missing entries before the effective boundary.
8. Mark those missing entries as removal candidates.
9. Ignore missing entries beyond the boundary.
10. Present the proposed changes for confirmation.

Use of anchors here avoids relying on raw line numbers when entries have been inserted or removed.
Avoid is treating the missing-entry heuristic as definitive. It should generate removal candidates
and never silently delete compatibility information.

That preserves the original objective: 
the tool should help maintain three runtime configurations without becoming another mod manager.

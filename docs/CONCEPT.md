# Concept of MOMM Application

## Modlist Manager

MO2 remains responsible for everything it already does well. The application only maintains runtime compatibility and synchronizes lists.

### 1. Data model

| Position | Name            | Type      | 1.5 | 1.6 | 1.7 | Active |
| -------- | --------------- | --------- | --- | --- | --- | ------ |
| 0        | Base            | Separator | —   | —   | —   | —      |
| 1        | USSEP 1.5       | Mod       | ✓   |     |     | ✓      |
| 2        | USSEP 1.6       | Mod       |     | ✓   |     | ✓      |
| 3        | USSEP 1.7       | Mod       |     |     | ✓   | ✓      |
| 4        | Address Library | Mod       |     | ✓   | ✓   | ✓      |
| 5        | JContainers NG  | Mod       | ✓   | ✓   | ✓   | ✓      |
| 6        | PapyrusUtil     | Mod       | ✓   | ✓   | ✓   |        |
| 7        | Base SKSE DLLs  | Separator | —   | —   | —   | —      |

Decisions:

- All three compatibility flags default to `true`.
- Separators have no compatibility flags.
- Active is imported from the original modlist.
- Position is determined by row order.
- Neither Active nor Position needs to be manually editable.
- Separators retain their original representation when exported.

I would not make Active an editable field in the first version. It is important to preserve the distinction between compatibility and activation.

### 2. The merger

This is a separate operation, with a preview before committing changes.

Merge workflow

1. Load source modlist.txt
   Parse names, separators, activation states and positions.

2. Compare with master list
   Identify new entries, existing entries and missing entries.

3. Add new entries (note that the engines will be configurable)
   Unknown entries receive compatibility flags `1.5 = true`, `1.6 = true`, `1.7 = true`.
   Their initial positions follow the source modlist.

4. Review missing entries
   Display previously known entries that aren't in the source.
   ! Missing doesn't necessarily mean obsolete. !

5. Resolve removal candidates
   All selected for removal by default with the ability to deselect entries that should be retained.
   Retained entries preserve their previous relative positions.

6. Commit merged list
   Update the master data only after confirmation.

One important complication: incomplete source lists

Use case:
Suppose a master contains 1,800 entries, but your 1.6.1170 installation contains only 1,500.
The import its modlist.

The 300 missing entries might be:

- Mods specific to 1.5.97.
- Mods specific to 1.7.104.
- Mods you simply haven't installed in this particular MO2 instance.
- Actually obsolete mods.

The application cannot distinguish these automatically.
-> Introduce a concept called source scope:

- Complete source: missing entries are removal candidates, selected by default.
- Partial source: missing entries are shown, but not selected by default.

This avoids accidentally deleting information from your master list.
It also means the application never needs mergerfs knowledge.
(fyi mergerfs is a user filesystem, Drivepool is an equivalent for Windows)

### 3. Position handling

Avoid maintaining numerical priorities internally.
Instead, use an ordered collection.
For example:

```
0  Base
1  USSEP
2  Address Library
3  Engine Fixes
4  Base SKSE DLLs
5  JContainers
6  PapyrusUtil
7  Main Mods
```

When exporting, enumerate the entries and write them in that order.
This is important because MO2's priority is ultimately represented by the line ordering in `modlist.txt`.
For merging, preserve the relative order of existing entries.

New entries should be inserted according to their position in the imported source list.
If an existing entry is absent from the source but retained during merging, keep its previous position relative to its surviving neighbours.
Separators must participate in exactly the same ordering mechanism as regular mods.

### 4. File formats

Two separate files will be used.

A. Master database: `modlist_master.csv`

```
Name,Type,1.5,1.6,1.7,Active      <- This is the header of the table (mainly for readability)
Base,separator,,,,                <- Separator deliberately without version establishment
USSEP 1.5,mod,1,0,0,1             <- Entries
USSEP 1.6,mod,0,1,0,1
USSEP 1.7,mod,0,0,1,1
Address Library,mod,0,1,1,1
JContainers NG,mod,1,1,1,1
PapyrusUtil,mod,1,1,1,0
```

The row ordering represents Position.
Retain the exact MO2 entry name, including spaces and special characters.

B. Application configuration: `settings.json`
Contains application settings.

For example:
Please note that using paths are still under discussion.
Preferably administrators only work with profiles, not with multiple instances.

```
{
    "version": 1,
    "recent_instances": [
        {
            "name": "Skyrim 1.5.97",
            "path": "/media/linux/1.5/MO2"
        },
        {
            "name": "Skyrim 1.6.1170",
            "path": "/media/linux/1.6/MO2"
        },
        {
            "name": "Skyrim 1.7.104",
            "path": "/media/linux/1.7/MO2"
        }
    ],
    "last_instance": "Skyrim 1.7.104"
}
```

This way a source MO2 installation is selectable without making the
application dependent on a particular filesystem layout.

Additional requirement: 
Make merging transactional. Never overwrite the master CSV or an MO2
modlist until validation succeeds. Create backups before writing.

### 5. UI: Console, Textual or Qt?

We use an incremental approach here.

a) Python CLI + Rich Text (idea, but read-only)

* Tables, colours and status indicators.
* Interactive merge confirmation.
* No graphical application dependencies.

b) Textual (limited interaction)

* Full-screen terminal interface.
* Sortable tables, checkboxes and keyboard navigation.
* Good fit for reviewing compatibility flags.

c) Qt / PySide6 (UI, full interaction)

* Native desktop application.
* Excellent table models and filtering.
* More implementation work.
* Probably unnecessary initially.

Full blown UI will be added in the second part. While
the release will have the UI already, the text variant
will remain as source of validation for developers or 
users that need such an output (f.e. for logging purposes)

The application logic will be separated from the UI. 
Implementation of the data model, parser, merger and 
exporter are independent parts. Switching from Textual
Qt will become straightforward (MVC principle)

### 6. Project architecture

```
mo2-modlist-manager/
│
├── main.py
├── settings.json
│
├── core/
│   ├── models.py
│   ├── parser.py
│   ├── exporter.py
│   ├── merger.py
│   ├── compatibility.py
│   └── validation.py
│
├── ui/
│   ├── console.py
│   ├── tables.py
│   └── dialogs.py
│
└── data/
    └── modlist_master.csv
```

Responsibilities:

| Module           | Responsibility                                                |
| ---------------- | ------------------------------------------------------------- |
| models.py        | Mod, separator and master list                                |
| parser.py        | Read MO2 modlist.txt                                          |
| exporter.py      | Generate runtime-specific lists                               |
| merger.py        | Compare and merge lists                                       |
| compatibility.py | Manage 1.5 / 1.6 / 1.7 flags                                  |
| validation.py    | Detect duplicate names, malformed entries and inconsistencies |

### 7. Suggested Implementation order

Could be done five stages:

1. Parser: Read modlist.txt, distinguish separators and mods, preserve active states and ordering.
2. Master database: Import into CSV, initialize all compatibility flags to true.
3. Exporter: Select 1.5, 1.6 or 1.7 and generate a valid MO2 modlist.txt.
4. Merger: Add new entries, identify missing entries, review removals and preserve positions.
5. Interactive UI: Rich console tables, filtering and compatibility toggles.

The exporter should be implemented early because it provides an excellent way to test whether parsing and serialization are correct.

## Important Architectural decisions

Master CSV is the authoritative compatibility database.
Master modlist.txt and it's iterative changes are the source of truth.

In particular:

- Compatibility belongs to the master database.
- Activation belongs to the imported MO2 list.
- Position belongs to the ordered master list.
- Filesystem existence is validation, not a prerequisite.

This way the application can become portable to other MO2 installations.

Design topic:
Importing a second source modlist should update the Active states of existing entries
or "Active" should remain unchanged unless explicitly imported as an update

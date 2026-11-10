# Final Software Design after Review Discussion

## Summary
Overall engine flexibility was increased, therefore
changes have been done in handling the game engines.

A backup extension was added after discussion of a
future feature for keeping more history information.

This is a very good extension of the concept. In fact,
consider moving from three hard-coded compatibility columns
to a configurable engine registry an important architectural
improvement, rather than just adding another setting.

It makes the application considerably more flexible without
making the user interface more complicated.

## Review
There are a few things that could be changed.

### 1. Configurable game engines

Approach is straightforward:

```
{
    "game_engines": [
        "1.5.97",
        "1.6.1130",
        "1.6.1170",
        "1.7.104"
    ]
}
```

The application reads this array and dynamically creates the corresponding compatibility columns.
For example: Compatibility overview. 
Illustrative master list with four configured engines

| Mod             | 1.5.97 | 1.6.1130 | 1.6.1170 | 1.7.104 |
| --------------- | ------ | -------- | -------- | ------- |
| USSEP 1.5       | ✓      |          |          |         |
| USSEP 1.6       |        | ✓        | ✓        |         |
| USSEP 1.7       |        |          |          | ✓       |
| Address Library |        | ✓        | ✓        | ✓       |
| JContainers NG  | ✓      | ✓        | ✓        | ✓       |
| PapyrusUtil     | ✓      | ✓        | ✓        | ✓       |

There is no reason to hard-code the number of engines in the application.
Keep the default configuration at three engines, but let the application
handle an arbitrary number of entries.

Consequently:

- No explicit VR functionality needs to be advertised.
- A VR maintainer can add Skyrim VR through configuration.
- Future Skyrim runtime versions require no application changes.
- The same application can support other configurations without branching the code.

One small improvement: Consider using objects rather than plain strings.

```
{
    "version": 1,
    "game_engines": [
        {
            "id": "skyrim-1.5.97",
            "name": "Skyrim 1.5.97",
            "version": "1.5.97"
        },
        {
            "id": "skyrim-1.6.1170",
            "name": "Skyrim 1.6.1170",
            "version": "1.6.1170"
        },
        {
            "id": "skyrim-1.7.104",
            "name": "Skyrim 1.7.104",
            "version": "1.7.104"
        }
    ]
}
```

Because the internal identifier and the displayed name don't necessarily have to be identical.
This becomes useful if entries are eventually wanted such as:

- Skyrim Special Edition 1.6.1170
- Skyrim VR
- Skyrim VR (custom runtime)
- Skyrim SE experimental installation

The application should use `id` internally and `name` for presentation.
No need to implement any additional functionality for this flexibility now.

### 2. An important consequence: the master database must become dynamic

Original concept uses a CSV with fixed columns:

```
Name,Type,1.5,1.6,1.7,Active
```

With configurable engines, those columns need to be generated dynamically.
This isn't particularly difficult, but it affects several components:

| Component        | Required adjustment                   |
| ---------------- | ------------------------------------- |
| models.py        | Dynamic compatibility mapping         |
| parser.py        | No engine-specific assumptions        |
| exporter.py      | Select engine by ID                   |
| merger.py        | Handle arbitrary compatibility fields |
| compatibility.py | Work with configured engines          |
| validation.py    | Validate against engine registry      |
| UI               | Generate columns dynamically          |

Change the underlying data model from fixed attributes:

```
mod.compat_1_5mod.compat_1_6mod.compat_1_7
```

To something like:

```
mod.compatibility = {    "skyrim-1.5.97": True,    "skyrim-1.6.1130": False,    "skyrim-1.6.1170": True,    "skyrim-1.7.104": True}
```

This is probably the single most important implementation change resulting from the concept.
Adding a fifth or sixth engine now doesn't require modifying the model classes.

### 3. What happens when engines are added or removed?

This is discussed here, but it right now a minor feature.
We already have opened up flexibility, so here is a proposed solution.

Imagine the maintainer initially uses:

```
"game_engines": [
    "1.5.97",
    "1.6.1170",
    "1.7.104"
]
```

Later, they add 1.6.1130.
What happens to existing mods?

The app could do:

- Existing compatibility information remains unchanged.
- The newly added engine receives an initial compatibility value for existing mods.
- The user can subsequently adjust individual entries.
- No existing compatibility information is deleted.

Important: According to original design new mods are initializes with all compatibility
flags set to `true`.&#x20;
This policy should be weakened when expanding the number of engines.

For example, when adding a new engine, assuming every existing mod is compatible might be misleading.
A safer alternative would be a three-state compatibility value:

| Value   | Meaning                 |
| ------- | ----------------------- |
| `true`  | Confirmed compatible    |
| `false` | Confirmed incompatible  |
| `null`  | Unknown / not evaluated |

Retaining the original default-true policy for newly imported mods if that is the deliberately prefered workflow.
Alternatively `unknown` could be used as the default for newly introduced engines or entries that changed that value.
A mod that has only one of it's columns set to true would be 'unknown'. If it is false it could be set to true.
This would avoid engine specific handling, but reduce the amount of maintenance decisions on each mod.

It prevents an unverified compatibility assumption from becoming an accidental export decision.

### 4. Settings.json should contain more than engine definitions

There should be more settings added to the configuration file.
This part was deliberately left open in the original concept because
settings was only about MO2 location and game engine definitions.

For example:

```

{
    "version": 1,

    "game_engines": [
        {
            "id": "skyrim-1.5.97",
            "name": "Skyrim 1.5.97",
            "version": "1.5.97"
        },
        {
            "id": "skyrim-1.6.1170",
            "name": "Skyrim 1.6.1170",
            "version": "1.6.1170"
        },
        {
            "id": "skyrim-1.7.104",
            "name": "Skyrim 1.7.104",
            "version": "1.7.104"
        }
    ],

    "instances": [],

    "storage": {
        "master_file": "momm-data/modlist_master.csv",
        "history_directory": "momm-data/history",
        "patch_directory": "momm-data/patches",
        "snapshot_directory": "momm-data/snapshots"
    },

    "backup": {
        "enabled": true,
        "keep_snapshots": 10,
        "preserve_imported_modlists": true
    },

    "merge": {
        "default_source_scope": "ask",
        "ignore_trailing_disabled_entries": true,
        "require_confirmation": true
    },

    "ui": {
        "show_incompatible_mods": true,
        "show_unknown_compatibility": true
    }
}

```

Definitions:

version
Configuration schema version. Important to later change the JSON structure.

instances
MO2 installation definitions. These should remain independent of the engine registry.

storage
Allows the user to change the data directory without modifying application code.

backup
backup concept, now configurable.

merge
These settings directly influence the merger's behaviour. 
`default_source_scope: ask`: when incomplete modlists are one of the more dangerous aspects of MOMM.

ui
Should be configurable rather than being hard-coded.

More will be added at a later point.

### 5. game engines versus MO2 instances

Game engines are the compatibility targets.

Example:
1.5.97
1.6.1130
1.6.1170
1.7.104

MO2 instances

Define the installations from which modlists are imported.

The Bad example (to show where confusion stems from):
Skyrim 1.5.97 → /path/to/MO2-1.5
Skyrim 1.6.1170 → /path/to/MO2-1.6
Skyrim VR → /path/to/MO2-VR

They are related, but they needn't to be the same thing.
Some modlist maintainer have instances for different releases.

This separation makes MOMM easier to extend.

### 6. Additional architectural considerations

There are four things to add to the original concept.

A. Never remove an engine automatically

If an engine is removed from `settings.json`, its compatibility
data should not disappear from the master database.

Instead, warn the user that the engine has existing data.
Ideally, distinguish between:

- Active engines: available for import/export.
- Retired engines: preserved in historical data but no longer selectable.

Because backups are available, the data can be removed at one point.
This should be done in a separate way to make sure that the user clearly
understands the consequences. A special backup shall be created for this case.

B. Make configuration changes transactional

When an engine is added, the application should:

1. Validate the configuration.
2. Compare the engine registry against the master database.
3. Identify new and retired engines.
4. Prepare the necessary database changes.
5. Back up the existing master.
6. Commit the changes.

Never leaving the master database with an incomplete compatibility mapping
makes the whole stored information saver. There are reasons why to make
handling of this data similar to a database:
a) A lot of work is in this data. A loss could mean days to weeks of restoration
b) The user gets aware of potential issue in MOMM, his system or other problems
   like change of access rights or Antivirus measurements preventing saving.
c) Even with backups in place the user may quickly want to sync and go.
   In a hectic situation mistakes are more likely and this is an additional
   step that makes it sure nothing serious happens while using the application.

C. Preserve unknown configuration fields

This is useful should optional settings or experimental features get introduced.
An older application version shouldn't unnecessarily destroy configuration entries
it doesn't understand when saving settings.

It remains important to inform the user that the version number is incorrect so
he sees that the version used does not match the stored version.

D. Keep settings and compatibility history separate

The settings file describes how the application operates.
The master database describes mod compatibility.

The patches describe changes to the master database.
This separation from your original design remains correct.

Nothingtheless backup of settings need to be made. 10 backups
will be done before overwriting the oldest. Should there be
a version mismatch, the original will be kept and renamed 
differently to avoid getting deleted by this process.

### 7. Overall assessment

A helpful and useful tool. By avoiding to use hardcoded values
and put them into settings or get them from game data, it will
get even more useful as long as it remains maintainable.

It makes sense to add the dynamic engine registry before 
implementing the compatibility system (i.e. part of Base).
This avoids a second round changing substantial parts of the tool.

Suggested (updated) development structure:

| Stage | Implementation                                  |
| ----- | ----------------------------------------------- |
| 1     | Settings loader, validation and engine registry |
| 2     | Dynamic data models                             |
| 3     | MO2 parser                                      |
| 4     | Master database and compatibility management    |
| 5     | Exporter                                        |
| 6     | Merger and partial-list detection               |
| 7     | History, patches and backups                    |
| 8     | Interactive UI                                  |

Settings and Game Data are still minimal enough to keep as classes
internally and CSV + JSON externally. SQLite starts making sense if
multiple tables that have certain dependencies and need a very good
performance need to be managed. Both is not the case for this tool,
a personal modlist maintenance helper.

With some of the planned feature or other ideas it may become necessary
to revise the structual underground, f.e. when there are multiple projects
to manage or extensive history management to do (f.e. each mod has
stored some kind of information that is slow to get or volatile)

A configurable-engine proposal improves the architecture considerably.
It makes the application extensible without turning it into a general-purpose
mod manager, which is precisely the boundary to preserve.

### 8 Extension: Backup

Goal: A minimal history of each mod - a feature not present in MO2. The known extension to me is cumbersome to use - an overview what has changed in a certain amount of time. For some reason the tool is fragile (I do rarely actually get this data even when I just installed a mod).

The history system in MO2 relies solely on Nexusmods. However Nexusmods provides information about changes in the mod, not about actually changed files. For conflict management this is often the first step if any plugin patches need to be done, assets need to be re-compressed, bsa files need to be rebuild, depending on what the modlist maintainer is doing.

The planned minimal history so far contains only the changed files which is in line with the tool context: mod files for different engines. SKSE files bring sometimes assets, often script and dll changes. On top the tool should be able to identify that the mod is actually a skse dll.

A few mods like USSEP have a strict Game dependency. Since this tool primary focus is on mods that are engine dependent, recognition of those other mods are not part any kind of recognition. They can be added when a specific engine is needed for a dll with features that only a certain release offers. Whilke any mod maintainer should avoid mods that are having a different sets of features, it sometimes goes unnoticed, so it is good to have these mods recognizable.

On UI side this will have a filter that only shows mods that only run on specific engines. With a system that checks mod content (a dll in
a specific folder) a mod can be marked as skse dll - one color (green) to indicate, the skse dll was checked an another (yellow/orange) that the mod was not checked by the maintainer.

The Backup does only need to store this information, when it is performance critical. This is useful for the indicator that a mod is a skse dll. Still on mod updates a check needs to be done if dll was added or removed. In this case and case of updates, the modlist maintainer needs to recheck the mod - the files alone do not indicate engine compatibility. It ensures that the mentioned compatibility is rechecked.  (In some specific versions MOD mod updates need to be avoided - a topic
which is not part of the tool maintenance at this time).

The history system should be event-oriented and extensible, rather than being designed exclusively around `modlist.txt` and CSV snapshots.
There are three additions to make to the concept.

#### Separate history events from stored files

For example:

```
momm-data/
├── master.csv
├── history/
│   ├── imports/
│   │   └── 2026-11-08_143500/
│   │       ├── modlist.txt
│   │       ├── source.csv
│   │       └── changes.json
│   │
│   ├── snapshots/
│   │   ├── master_2026-11-08_143500.csv
│   │   └── master_2026-11-08_161200.csv
│   │
│   └── mods/
│       └── Example Mod/
│           └── 2026-11-08_170000/
│               └── manifest.json
│
└── patches/
    ├── 0001.json
    └── 0002.json
```

The `mods` directory is reserved for future expansion.
No need to implement it now.

#### Future mod-file history

Use a file manifest containing:

| Property               | Purpose                                              |
| ---------------------- | ---------------------------------------------------- |
| Relative path          | Identify the file                                    |
| Modification timestamp | Detect changed files                                 |
| File size              | Detect many changes even if timestamps are preserved |
| Optional hash          | Verify changes when necessary                        |

For example:

```
{
    "mod": "Example Mod",
    "captured_at": "2026-11-08T17:00:00",
    "files": [
        {
            "path": "SKSE/Plugins/example.dll",
            "mtime": 1794153600,
            "size": 245760
        },
        {
            "path": "meshes/example.nif",
            "mtime": 1794153600,
            "size": 81920
        }
    ]
}
```

A comparison between manifests could classify files as:

- Added
- Removed
- Modified (timestamp or size changed)
- Unchanged

No content-level diff is necessary.
Caveat: timestamps alone aren't entirely reliable. File size
is a cheap additional check. Hashing can remain optional for
cases where stronger verification is needed. File size check
shall be added if content often is found to have changed without
file date change (rather unlikely).

#### Make backup policies independent

Avoid having one global retention policy for everything.

For example:

| History type               | Retention                |
| -------------------------- | ------------------------ |
| Original imported modlists | Permanent                |
| Master patches             | Permanent                |
| Full master snapshots      | Configurable, default 10 |
| Mod-file manifests         | Configurable, future     |
| Actual mod-file backups    | Configurable, future     |

This prevents an eventual cleanup operation from accidentally 
deleting original imported modlists or patches.

#### Architectural consequence

Introduce a small history interface early, even if initially it only
supports modlist imports and master changes.

Conceptually:

```
class HistoryManager:    def record_import(self, source, parsed_data):        
...    def record_master_change(self, patch):        
...    def create_snapshot(self, master):        
...    # Future:    def record_mod_manifest(self, mod_path):        
...
```

The future methods don't need implementation now. The important thing is that the rest of the application doesn't need to know how history is physically stored.

Recommendation: Keep CSV as the current master format, JSON for patches and manifests, and original MO2 files as immutable historical inputs.

For this SQLite isn't needed. The proposed system is still small enough for ordinary files, and those files have an important advantage: they remain independently readable, inspectable and manually editable.

The history architecture should anticipate mod-file tracking, but the first release should focus exclusively on modlist history and compatibility management.

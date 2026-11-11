# Use case overview

For any UI it's always helpful to look at the Use Cases as a reference.

A small sequence of how a feature of UI is used is the base for systematic test of the whole application.

This document is divided into several parts that are structured by frequency of use - this way the most often used functionality is not broken when checking any update.

To not loose complete overview on top there are rather rough sections that reflect the UI parts.

## MOMM – MO2 Modlist Merger
### Use Case Overview

**Project:** MOMM (MO2 Modlist Merger)
**Document:** Use Case Overview  
**Status:** Initial concept  
**Purpose:** UI design reference and basis for systematic application testing

---

## 1. Application Overview

MOMM manages compatibility information and merges MO2 modlists for different Skyrim game engine versions.

It does not replace MO2 and does not attempt to manage installed mods, plugins, executables or game configurations.

Its primary responsibilities are:

- Maintaining a central modlist database.
- Managing compatibility across configurable game engines.
- Importing existing MO2 modlists.
- Comparing and merging modlists.
- Exporting engine-specific modlists.
- Maintaining a history of imports and database changes.
- Providing backups and recovery mechanisms.

The application operates independently of the underlying filesystem structure. It must not depend on mergerfs or any specific MO2 installation layout.

# 2. UI Structure

The following sections represent the proposed major areas of the application.

| Section | Purpose | Frequency |
|---|---|---|
| 1. Overview | Current database and application status | High |
| 2. Modlist Management | View and maintain the main list | Very high |
| 3. Import & Merge | Import and reconcile MO2 modlists | High |
| 4. Export | Generate engine-specific modlists | High |
| 5. History | Review imports, changes and snapshots | Medium |
| 6. Configuration | Manage engines, MO2 instances and paths | Low |
| 7. Maintenance | Backups, validation and recovery | Low |

The frequency classification is preliminary and can be adjusted after practical use.

---

# 3. Use Cases

## 3.1 Overview and Startup

### UC-001 – Start MOMM

**Purpose:** Initialize the application and load its current state.

Sequence:
1. Start MOMM.
2. Load settings.json.
3. Validate the configuration.
4. Load the main list database.
5. Check the database against the configured engine registry.
6. Display the overview.

Expected result:
- Application is ready for use.
- Configuration or database problems are reported.
- No existing data is modified during startup.

### UC-002 – Select an MO2 instance

**Purpose:** Select the installation used for importing or exporting.

Sequence:
1. Open the instance selector.
2. Select an existing MO2 instance.
3. Display its name and configured path.
4. Verify that the expected MO2 profile directory is accessible.

Expected result:
- The selected instance becomes the current working instance.
- The selection does not change the main list database.

### UC-003 – Review application status

**Purpose:** Obtain an overview of the current data.

Display information:
- Number of mods.
- Number of separators.
- Number of configured game engines.
- Last import.
- Last main list modification.
- Last snapshot.
- Pending or unresolved changes, if any.

Expected result:
- User can quickly identify the current state of MOMM.

---

## 3.2 Modlist Management

This is the primary area for maintaining compatibility information.

### UC-010 – Display main list

**Purpose:** Display the complete main modlist.

Sequence:
1. Open Modlist Management.
2. Load all entries in their stored order.
3. Display the compatibility columns dynamically from the engine registry.

Displayed information:

| Field | Description |
|---|---|
| Position | Current ordering |
| Name | Exact MO2 mod name |
| Type | Mod or separator |
| Compatibility | One column per configured engine |
| Active | Activation state, where available |

Expected result:
- Separators are visually distinguishable.
- Original ordering is preserved.
- Compatibility information is displayed correctly.

### UC-011 – Change mod compatibility

**Purpose:** Mark a mod as compatible or incompatible with a game engine.

Sequence:
1. Select a mod.
2. Select its compatibility value for an engine.
3. Change the value.
4. Save the modification.

Expected result:
- Only the selected compatibility value changes.
- Other engines remain unchanged.
- The change is recorded in the patch history.

Compatibility values:
- True: Compatible.
- False: Incompatible.
- Unknown: Not evaluated.

### UC-012 – Review unknown compatibility

**Purpose:** Identify mods whose compatibility has not been established.

Sequence:
1. Activate the unknown-compatibility filter.
2. Display affected mods.
3. Review their compatibility values.

Expected result:
- Unknown entries can be identified without inspecting every mod.

### UC-013 – Filter and search mods

**Purpose:** Find specific entries in a large main list.

Possible filters:
- Mod name.
- Separator.
- Compatible with selected engine.
- Incompatible with selected engine.
- Unknown compatibility.
- Active or inactive.
- Position or category.

Expected result:
- Filtering does not change stored ordering or data.

### UC-014 – Inspect a mod entry

**Purpose:** Review the stored information for a particular mod.

Display:
- Exact mod name.
- Type.
- Position.
- Compatibility values.
- Current activation state, if available.
- Related history entries, if available.

No direct filesystem modifications are performed.

---

## 3.3 Import & Merge

This section is responsible for reconciling existing MO2 modlists with the main list database.

### UC-020 – Import an MO2 modlist

**Purpose:** Read an existing modlist.txt.

Sequence:
1. Select an MO2 instance.
2. Select an MO2 profile.
3. Load its modlist.txt.
4. Parse entries, separators, active states and ordering.
5. Validate the parsed data.
6. Preserve the original imported file.
7. Create a parsed source snapshot.

Expected result:
- The original file remains unchanged.
- The imported list is available for comparison.
- Import metadata is recorded.

### UC-021 – Detect new entries

**Purpose:** Find entries in the imported list that do not exist in the main list database.

Sequence:
1. Compare imported entries with main list entries.
2. Match by exact mod name.
3. Identify unknown entries.
4. Add them to the proposed merge.
5. Initialize their compatibility values to true for all configured engines.

Expected result:
- New entries are clearly identified.
- Existing main list entries are not duplicated.
- New entries retain their source ordering.

### UC-022 – Detect missing entries

**Purpose:** Identify main list entries absent from the imported list.

Sequence:
1. Compare main list entries with imported entries.
2. Establish positional anchors.
3. Determine the effective list boundary.
4. Identify missing entries before the boundary.
5. Ignore missing entries beyond the boundary.

Expected result:
- Potential removals are identified.
- Missing entries are not automatically deleted.
- The user can review the proposed changes.

### UC-023 – Select source scope

**Purpose:** Specify whether the imported list represents a complete or partial installation.

Available choices:
- Complete source.
- Partial source.
- Ask / determine manually.

Expected result:
- The selected scope influences missing-entry detection.
- Partial lists do not automatically cause unrelated main list entries to be removed.

### UC-024 – Handle trailing disabled entries

**Purpose:** Detect partial modlists where trailing entries are disabled.

Sequence:
1. Inspect the imported ordering.
2. Identify the continuous trailing sequence of disabled entries.
3. Determine the effective boundary.
4. Treat missing entries beyond that boundary as ignored.

Expected result:
- Disabled trailing entries do not incorrectly extend the effective boundary.
- Disabled entries in the middle of the list remain part of the positional comparison.

### UC-025 – Review merge candidates

**Purpose:** Review all proposed changes before committing.

Display:
- New entries.
- Existing entries.
- Missing entries.
- Removal candidates.
- Retained entries.
- Compatibility changes, if applicable.
- Position changes.

Expected result:
- User can accept or reject individual proposed removals.
- No main list data is modified before confirmation.

### UC-026 – Commit merge

**Purpose:** Apply an approved merge.

Sequence:
1. Validate the proposed result.
2. Create a backup of the current main list.
3. Generate the corresponding patch.
4. Apply the changes.
5. Save the updated main list.
6. Record the import and merge event.

Expected result:
- Main list database contains the approved changes.
- Previous state remains recoverable.
- Original imported modlist remains preserved.

### UC-027 – Cancel merge

**Purpose:** Discard an uncommitted merge.

Sequence:
1. Cancel the merge preview.
2. Discard proposed changes.
3. Return to the previous state.

Expected result:
- Main list database remains unchanged.
- Imported source and its history remain available.

---

## 3.4 Export

### UC-030 – Export modlist for a game engine

**Purpose:** Generate an MO2 modlist.txt for a selected engine.

Sequence:
1. Select a configured game engine.
2. Select the target MO2 instance and profile.
3. Filter the main list list using the selected engine's compatibility.
4. Preserve the original ordering.
5. Preserve separators.
6. Preserve activation states.
7. Generate modlist.txt.

Expected result:
- Only entries compatible with the selected engine are exported.
- Incompatible entries are excluded.
- Unknown compatibility is handled explicitly.
- The generated file uses valid MO2 formatting.

### UC-031 – Review export

**Purpose:** Inspect the resulting modlist before writing it.

Display:
- Total entries.
- Number of mods.
- Number of separators.
- Excluded incompatible entries.
- Excluded unknown entries.
- Active and inactive counts.

Expected result:
- User can detect unexpected exclusions before exporting.

### UC-032 – Save exported modlist

**Purpose:** Write the generated file to the selected MO2 profile.

Sequence:
1. Confirm the destination.
2. Preserve an existing destination file if necessary.
3. Write the new modlist.txt.
4. Verify the resulting file.

Expected result:
- Target profile receives the generated modlist.
- Previous destination data can be recovered.

---

## 3.5 History and Change Tracking

### UC-040 – Review import history

**Purpose:** Inspect previously imported modlists.

Display:
- Import timestamp.
- Original filename.
- Source MO2 instance.
- Source profile.
- Source file modification timestamp.
- Import result.

Expected result:
- Previous imports can be identified and inspected.

### UC-041 – Inspect an imported modlist

**Purpose:** Review a historical source.

Sequence:
1. Select an import event.
2. Open its preserved original modlist.txt.
3. Display the parsed source snapshot.

Expected result:
- Historical data can be reviewed without changing the current main list.

### UC-042 – Review main list changes

**Purpose:** Inspect modifications made to the main list database.

Display:
- Change timestamp.
- Operation.
- Affected mod.
- Previous value.
- New value.
- Related patch.

Expected result:
- Individual changes can be traced.

### UC-043 – Review main list snapshots

**Purpose:** Inspect previously saved full database states.

Sequence:
1. Open snapshot history.
2. Select a snapshot.
3. Display its contents or compare it with the current main list.

Expected result:
- Historical main list states remain independently readable.

### UC-044 – Restore a previous main list state

**Purpose:** Recover from an unwanted change.

Sequence:
1. Select a historical snapshot.
2. Review the differences.
3. Confirm restoration.
4. Create a backup of the current main list.
5. Restore the selected state.
6. Record the restoration as a new history event.

Expected result:
- Previous data is recovered.
- Existing history is not erased.
- Restoration itself is traceable.

---

## 3.6 Configuration

### UC-050 – Configure game engines

**Purpose:** Maintain the dynamic engine registry.

Sequence:
1. Open Configuration.
2. Display configured engines.
3. Add, edit or retire an engine.
4. Validate engine IDs and names.
5. Reconcile compatibility mappings.
6. Save configuration and database changes transactionally.

Expected result:
- Compatibility columns are generated dynamically.
- Existing compatibility information is preserved.
- Newly introduced engines receive an explicit unknown compatibility state where appropriate.
- Retired engines remain in historical data.

### UC-051 – Configure MO2 instances

**Purpose:** Maintain known MO2 installations.

Sequence:
1. Open instance configuration.
2. Add or edit an instance.
3. Set its display name and filesystem path.
4. Validate the path.
5. Save the instance.

Expected result:
- Instances can be selected independently of game engine definitions.
- Multiple instances may reference the same engine.

### UC-052 – Configure storage paths

**Purpose:** Change MOMM's storage locations.

Configurable locations:
- Main list database.
- History directory.
- Patch directory.
- Snapshot directory.

Expected result:
- MOMM uses the configured locations.
- Existing data is not moved or deleted without explicit confirmation.

### UC-053 – Configure merge defaults

**Purpose:** Define default merge behaviour.

Settings:
- Default source scope.
- Ignore trailing disabled entries.
- Require merge confirmation.

Expected result:
- Default behaviour is applied consistently.
- Important decisions remain visible to the user.

---

## 3.7 Maintenance and Validation

### UC-060 – Validate main list database

**Purpose:** Check database integrity.

Checks:
- Duplicate mod names.
- Invalid entry types.
- Missing compatibility mappings.
- Invalid engine references.
- Invalid ordering.
- Malformed records.

Expected result:
- Problems are reported without modifying data.

### UC-061 – Validate configuration

**Purpose:** Check settings.json.

Checks:
- Configuration schema version.
- Engine IDs.
- Duplicate instances.
- Storage paths.
- Invalid merge settings.

Expected result:
- Invalid configuration is reported before it can damage existing data.

### UC-062 – Create backup

**Purpose:** Save a recoverable database state.

Sequence:
1. Create a full main list snapshot.
2. Store it with a timestamp.
3. Update snapshot retention.
4. Preserve permanent history records.

Expected result:
- A recoverable main list snapshot exists.

### UC-063 – Recover from invalid data

**Purpose:** Recover after an unsuccessful write or corrupted database.

Sequence:
1. Detect invalid main list data.
2. Prevent further modifications.
3. Identify the most recent valid snapshot.
4. Offer recovery.
5. Preserve the invalid source for diagnosis.

Expected result:
- Existing data is not silently overwritten.

---

# 4. Future Extensions

The following functionality is anticipated by the architecture but is not part of the initial implementation.

## UC-070 – Track mod-file changes

Purpose: Maintain lightweight file history for individual installed mods.

Potential sequence:
1. Select a mod.
2. Scan its directory.
3. Create a file manifest.
4. Compare it with the previous manifest.
5. Identify added, removed and modified files.

Comparison properties:
- Relative file path.
- Modification timestamp.
- File size.
- Optional hash.

A full content diff is not required.

## UC-071 – Review mod-file history

Purpose: Inspect historical changes to an individual mod.

Display:
- Capture timestamp.
- Added files.
- Removed files.
- Modified files.
- Previous manifests.

Actual file backups and restoration can be considered separately.

---

# 5. Testing Strategy

Use cases should also serve as the basis for systematic regression testing.

The recommended testing order follows their frequency and importance.

| Test group | Use cases | Priority |
|---|---|---|
| Startup | UC-001 to UC-003 | High |
| Modlist management | UC-010 to UC-014 | Very high |
| Import & merge | UC-020 to UC-027 | Very high |
| Export | UC-030 to UC-032 | Very high |
| History | UC-040 to UC-044 | Medium |
| Configuration | UC-050 to UC-053 | Medium |
| Maintenance | UC-060 to UC-063 | Medium |
| Future extensions | UC-070 to UC-071 | Later |

## Essential regression scenarios

The following scenarios deserve particular attention:

1. Import an unchanged MO2 modlist.
2. Import a modlist containing new mods.
3. Import a modlist missing version-specific mods.
4. Import a partial modlist.
5. Import a modlist with trailing disabled entries.
6. Import a modlist with disabled entries in the middle.
7. Merge lists with different separator positions.
8. Export each configured engine.
9. Export with unknown compatibility entries.
10. Add a new engine without losing existing compatibility information.
11. Retire an engine without deleting its historical data.
12. Restore a previous main list snapshot.

All operations that modify persistent data should additionally be tested for cancellation, validation failure and unsuccessful writes.

---

# 6. General Design Principles

The following principles apply throughout MOMM:

1. **MO2 remains authoritative for mod installation and activation.**
2. **MOMM maintains compatibility and main list ordering.**
3. Original imported modlists are immutable historical inputs.
4. Compatibility is independent of activation.
5. Separators are first-class ordered entries.
6. Game engines are dynamically configured.
7. MO2 instances and game engines are independent concepts.
8. No filesystem layout or mergerfs dependency is assumed.
9. Changes to persistent data are recorded and recoverable.
10. User confirmation is required before committing merges and destructive operations.

The UI should make important decisions visible without attempting to reproduce all of MO2's functionality.

**End of initial use case overview.**

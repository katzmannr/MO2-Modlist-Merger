# MOMM — Part 3: User Interface

Part3 defines Frontend of MO2 Modlist Merger, it's basic architecture.
It uses Interface of MOMM - Backend, avoiding duplicating backend responsibilities.

## 1. Scope and principles

The UI is responsible for:
* Displaying settings and modlist information.
* Collecting user information.
* Presenting backend validation errors and operation results.
* Assign operations to backend.
* Confirming potentially destructive operations.
* Notifying the user of unfinished work.

The backend remains responsible for:
* Parsing and exporting MO2 modlists.
* Maintaining compatibility lists.
* Validating lists.
* Import and merge MO2 modlist.
* Storing of main list CSV.
* Integrating known engine list CSV into loaded main list ("Knowledge database)
* Merging, backup, snapshots and history.
* Stepwise changes and rollback or cleanup on errors.

The UI shall not independently reinterpret or modify the modlist order or main list data.
All operations are performed using it's backend.

### 1.1 Technical Requirements for use

* Python 3.10 or newer.
* PySide6.
* Qt Quick / QML.
* Qt Quick Controls and Layouts.
* C++ shall be avoided (any use must be explicitely documented and established).
* Information comes solely from backend (MO2), not Nexusmods or other Internet sources

The goal is that the information which skse mod supports which engine is provided by the user.

Consequently the user needs to regularly check for updates on engine changes.

There can be multiple, differently named, skse mods that solely exists for specific engine versions.

Neither backend nor frontend check duplicate mod or dll entries (this is MO2 responsibility)
The tool shall not expose specific engine compatibility issues. This remains responsibility of mod authors.

Example: assume we have a mod named enginefixes.
Such a mod can come in many variants:
* support only one engine
* support only one engine for a specific engine (no multi-engine-version support)
* support multiple but not all engines

QML handles presentation and interaction. Python exposes backend operations and application state through a small interface layer.

### 1.2 Proposed frontend source structure

```text
src/
├── MOMM_backend/
│   └── ...
│
├── MOMM_frontend/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py
│   ├── backend_interface.py
│   ├── main_list_model.py
│   │
│   └── qml/
│       ├── Main.qml
│       │
│       ├── components/
│       │   ├── TopNavigation.qml
│       │   └── StatusResult.qml
│       │
│       └── pages/
│           ├── SettingsPage.qml
│           ├── MainListPage.qml
│           ├── HistoryPage.qml
│           └── BackupPage.qml
│
├── PART1-BASE.md
├── PART2-BACKEND.md
└── PART3-USERINTERFACE.md
```

## 2. Common UI elements

This part explains the UI pages and elements that can be used by those pages.

### 2.1 Main navigation

The application has four pages:

1. Settings
2. Main List
3. Backup
4. History

The current page is deliberately omitted from the navigation controls. For example, when Main List is open, the navigation offers Settings, Backup and History.

The default navigation presentation uses text. A long press switches between text and icon presentation. The selected presentation is stored in UI settings.

The navigation must:
* Remain available on every page.
* Use the same position and visual style.
* Avoid dropdown menus.
* Avoid a separate overview page.
* Preserve the current page when switching between text and icon presentation.

All long-press shall have an indicator showing when the action behind can be done.

(fyi moving finger/mouse away still can cancel the action which is standard behavior,
the UI shall not explicitely assume an action from "press" alone)

When talking about "tap" this is always interchangeable with click on desktop or a mouse connected to a mobile.

### 2.2 Status and result element

A shared status element is displayed at the bottom of the application.

It provides:
* A short status or most recent message.
* An indication when there are errors or warnings.
* A long-press action to collapse the result to one line.
* A tap action to open the complete message view (results from backend operation).

The message view supports:
* Reading individual messages.
* Removing an individual message.
* Clearing all messages after confirmation.

The result area is shared by all pages. Page-specific error handling should use the same reporting mechanism.

### 2.3 Shared interaction rules

* Use platform-native text editing and on-screen keyboards.
* Avoid custom confirmation buttons for ordinary text fields.
* Keep existing text, so it can be edited.
* Validate settings immediately.
* Save settings when the user finishes changing a value.
* Preserve normal keyboard undo behaviour.
* Require confirmation before destructive operations.
* Do not discard unfinished Main List changes.
* Keep text contrast sufficient in all entry states.

## 3. Settings page

### Purpose

The Settings page modifies the application's configuration.

(it uses JSON as format, handled by backend.)

The layout is dynamically generated from the settings structure. It must not depend on a fixed list of engine versions or hard-coded compatibility columns.

### 3.1 General settings

Display settings as a flat list of labels and values rather than a deeply nested tree.

For example:

| Group | Setting |
|---|---|
| Storage | Main CSV file |
| Storage | \<History directory\> |
| Storage | \<Patch directory\> |
| Storage | \<Snapshot directory\> |
| Backup | Enabled |
| Backup | Snapshot storage |
| Merge | Default source scope |
| Merge | \<MO2 directory\>
| Merge | Enable Automatic Mod Removal |

Data Lists and structured values may use a dedicated selector or editor where appropriate.

### 3.2 Game engines

Game engines are selected through a listbox or equivalent selector.

The selected engine's properties are displayed alongside it:
* Engine ID
* Display name
* Version
* Status

The engine list is generated from the engine registry. Actually Version and Status is enough (more is not used in main list).

Adding, retiring or modifying an engine must use backend validation and must preserve existing compatibility data.

### 3.3 UI settings

UI settings are hidden by default.

Selecting the UI section reveals them. This keeps the normal settings page compact and makes it clear that these options control the interface rather than the data model.

### 3.4 Profiles

MO2 has a great profile feature and this application makes use of it. Reading of known profiles
is done by the backend on startup. Manually adding/removing profiles is not supported.

This operation replaces the main list csv after a backup was created. A warning is only shown
when the review was not finished.

Profiles are recommended to have differend modlist for each engine. The user is expected to have
three different profiles when he has declared three engines in the settings.

On top partial list handling is no longer needed. Any change from modlist.txt from the selected
profiles (additions and deletions) is taken over. Removal needs to be confirmed.

### 3.5 Persistence and validation

There is no general Save button.

A changed value is validated and persisted when editing is completed. Invalid values are reported immediately.

When a save failed because of edit, the previous value is restored. For other issues the application should avoid restoring anything. The backend will update main list when necessary.

## 4. Main List page

### Purpose

The Main List is the primary working page. It displays all entries in the exact order maintained by the backend.

The order must not be changed by the UI.

### 4.1 Displayed information

Each normal entry displays:
* Mod name.
* One compatibility value for each configured engine.
* SKSE/DLL classification.
* Review status.

Engine columns are generated dynamically from the engine registry (backend).

Separators are displayed as distinct entries and do not have compatibility controls.

### 4.2 Entry presentation

The intended visual states are:

| Appearance | Meaning |
|---|---|
| White | Normal mod |
| Green | SKSE/DLL mod reviewed by the user |
| Yellow | SKSE/DLL mod awaiting review |
| Grey | Separator |

The backend's DLL classification is authoritative and is not editable by the user.

### 4.3 Compatibility interaction

Engine compatibility has three values:

* Unknown (i.e. not decided by the user)
* Compatible
* Incompatible

The UI must make these states visually distinguishable.

The user compatibility change for an individual engine does not affect other engines.

### 4.4 Review workflow

The review marker is separate from compatibility itself.

The marker determines that the user as decided on each engine compatibility.

The marker can be made dependent on those decisions when it was unknown.

A change in a skse dll needs a new confirmation by the user (backend information).

The shared status element may display a general review warning when unresolved SKSE/DLL entries remain.

### 4.5 Refresh and merge

The user can refresh the Main List from a MO2 source.

The backend prepares a non-destructive merge preview. The UI must present:
* New entries.
* Missing entries.
* Warnings.

Missing entries must never be automatically deleted. Should the backend find out, that a partial list shall be merged,
the user must confirm a warning that the modified list will be integrated into the existing main list. 
The warning message shows that \<amount\> entries of the existing main list will be removed.

The warning message says
"By keeping the deleted mods from modlist.txt you are responsible for restoring those mods in your profile."
(or a similar shorter message). The extra message should be marked (f.e. bold letters)
The message buttons should be "Still Keep" and "Remove".

There should be a short delay before the user can confirm the removal.

The original imported `modlist.txt` remains unchanged.

After a successful merge, affected entries must be reviewed again where required by the backend workflow.

### 4.6 Sections

When the list exceeds the available display area:
* Use explicit section numbers.
* Provide Previous and Next controls.
* Provide a direct section choice.
* Do not rely on scrollbar markers as the primary navigation mechanism.
* Mouse Wheel can be used to navigate between sections (not entries)

The initial release does not provide mod-type filtering on the editable Main List page.

### 4.7 Switching pages and unfinished work

Before leaving the Main List, the application checks whether there are unfinished changes.

The user must be informed and asked to confirm the operation when necessary.

The UI must not discard unfinished work.

## 5. History page

### Purpose

History is the archive of original MO2 `modlist.txt` imports.

It is an emergency/reference view, not another editable Main List.

### 5.1 Contents

Each archived import should be selectable and displayed in read-only list form.
The original imported file must remain unchanged.

An archived entry can be compared against the latest modlist.txt which forms
the base of the current main.csv. Two archived entries can be compared against
each other. 

### 5.2 Filters

History supports filters for:
* SKSE/DLL mods.
* Non-SKSE mods.
* Separators and other non-mod entries.

The corresponding entry presentation uses:
* Green for SKSE/DLL mods.
* White for ordinary mods.
* Grey for separators.

### 5.3 Restrictions

History does not:
* Edit the archived list.
* Compare an archived MO2 list directly with the current Main List.
* Replace the merge process.
* Display old main-list CSV snapshots.

A future version may add comparison between imported MO2 lists. This is not part of the initial UI.

### 5.4 Comparison (future feature).

The comparison view should be a simple side-by-side comparison
marking only changed entries.

Overlang lines can be truncated or put into a new line. Scrolling should be avoided.
The navigations between sections follows the same scheme as in main list page.

Alternatively an external diff program could be considered like kdiff3.

## 6. Backup page

### Purpose

Backup is for MOMM's own main-list data, not original MO2 `modlist.txt` imports.

It displays saved main-list CSV files and snapshots in read-only form.

### 6.1 Available operations

**New**

Creates a user backup of either the current Main List or a selected existing backup.

**Use**

Restores a selected backup as the current Main List.

Before restoration:
* Show a confirmation.
* Back up the current Main List.
* Preserve the previous state.
* Record the restoration through the backend history mechanism.

**Compare**

Displays differences between a selected backup and the current Main List.

The comparison initially supports:
* All entries.
* SKSE/DLL entries only.

Overlang lines can be truncated or put into a new line. Scrolling should be avoided.
The navigations between sections follows the same scheme as in main list page.

Alternatively an external diff program could be considered like kdiff3.

### 6.2 Read-only display

The backup view uses the same row presentation as the Main List.

The difference is that entries cannot be edited.

### 6.3 Automatic snapshots

Automatic snapshots protect against accidental loss of recent work.

The default interval is five finished edit steps. The number of steps is configurable.
One edit step corresponds a review of one mod entry.

A warning should be displayed when the configured interval is three or fewer steps, because this reduces the amount of recent work that can be recovered through snapshots.

Snapshot creation and storage must be controlled by the backend.

### 6.4 Extract and Integrate

The User can extract all skse mods into a csv that can be used with oder modlists.
Integration of this information can be done while working with a different main list.

The History allows to have user-defined local modlist.txt that are different or partial.
The user can only merge these into the existing ones.

The Backup creates Snapshots and Full backups. Removing backups is done automatically
under conditions defined from confugartion. A manual removal of main list is not planned.

The user can integrate this special skse mod list csv into the existing mod with using "Integrate"
In contrast to normal merge, no mods will be added to the main list, but only the information
about skse mod lists will be added (special backend handling).

The Backup treats this skse mod list generally as any other mod list (not allowing to simply
overwrite the previously extracted skse mod list, so the only difference is the name.

## 7. Desktop and mobile behaviour

The desktop is the primary platform.

Mobile use is supported, with tablets as the primary mobile target.

The mobile interface should retain the same general aspect ratio and information layout as the desktop interface.

Do not introduce a compact mode that removes compatibility columns or requires a separate detail screen for every mod. The information density and interaction model should remain consistent.

## 8. Backend integration interface

The frontend should communicate with the existing backend through a narrow Python interface.

The interface exposes:
* Settings and engine registry.
* Main List model.
* Status messages.
* Import and merge operations.
* History entries.
* Backup entries and operations.

QML should not access CSV or JSON files directly.

The backend remains the authority for validation, persistence and rollback.

### 8.1 Current backend integration notes

The current backend already provides:
* `AppSettings` and settings load/save functions.
* `MainModlist` and `ModlistEntry`.
* `MainRepository`.
* `HistoryManager`.
* Dynamic engine compatibility.
* Review workflow metadata.
* Import parsing and export.
* Non-destructive merge previews.

The initial UI should use these existing components rather than reimplementing them.

### 8.2 Items requiring backend alignment

Before enabling all editing and backup actions, the following backend details need to be upgraded:

1. `HistoryManager` currently derives its snapshot and patch directories from the history root. The settings structure also contains separate `snapshot_directory` and `patch_directory` values. These paths should eventually be respected consistently.
2. `MainRepository.commit()` currently creates a snapshot for every commit. The UX design specifies snapshots after a configurable number of finished edits. The backend needs an edit-step policy before the UI can rely on that behaviour.
3. The UI's SKSE review interaction and the backend's `has_dll` / `review_status` fields must remain distinct. DLL classification is not user-editable; review status is not compatibility.
4. The Backup page's named user backups, restore and compare actions need a complete backend-facing operation contract. The existing snapshot mechanism alone does not implement all three actions.

These are integration tasks, not reasons to duplicate backend logic in QML.

## 9. Initial implementation stages

### Part 3.1 — Base and common UI

* Application entry point.
* PySide6/QML startup.
* Backend interface.
* Main window.
* Shared navigation.
* Shared status/result element.
* Four page containers.

### Part 3.2 — Settings page

* Dynamic settings display.
* Engine selector.
* UI settings visibility.
* Immediate validation and persistence.

### Part 3.3 — Main List page

* Dynamic engine columns.
* Ordered entries.
* Entry colours and review markers.
* Section handling.
* Compatibility editing.
* Merge preview and confirmation.
* Unfinished-work protection.

### Part 3.4 — History page

* Import archive listing.
* Read-only source list.
* Entry-type filters.

### Part 3.5 — Backup page

* Snapshot and backup listing.
* Read-only list display.
* New backup.
* Restore.
* Compare.

## 10. Acceptance criteria for the first UI alpha

* The application starts using PySide6.
* All four pages can be opened.
* Navigation is consistent.
* Navigation text/icon presentation can be switched.
* The shared status area is visible and can show diagnostics.
* Settings and engine definitions can be read from the existing configuration.
* The Main List can be loaded and displayed in its stored order.
* Dynamic engine columns are supported.
* History and Backup are visibly separate.
* No UI operation silently changes or deletes stored data.

The first alpha prioritizes a reliable shared shell and correct data presentation. Editing and destructive operations should be enabled only when their backend contracts are ready.

# User Experience - Look and Feel of MOMM

MOMM - MO2 Modlist (Engine) Manager is a tool handling a
specific use case: Supported Engine mods. The UI follows
some drastically different way that are more compatible
on all platforms.

## Top

The entry ideally shows the list of all mods similar to MO2 itself - but now settings or buttons. Similar to mobile apps but part of the UI there is a possibiltiy
to navigate to certain parts.

The Top of the program contains Text or Graphical Buttons to enter specific parts of the app.

For MOMM this are Settings, Modlist, Backup, History.

## Settings

Settings: Modify the Settings file - the UI itself depends on
the Settings structure. It is dynamically created with fixed
properties following json principles.

The top in our case is the list of entries that can be changed.

This results in a layout where each entry is shown.

Entries are either single values or arrays. They look very similar.

For example "version" is just a string field.
Each entry "storage" is on the same line, so you do not see a tree but
storage - main csv file
storage - history directory
etc. with string fields

game engines are the exception. Since the screen space is limited, 
we use a listbox where you select the engine.
The entries are on the right side of the listbox. 
The entries are updated after selection.

There is no "save" button. Entries are updated as soon as the
user leaves the field. Validity checks are performed immediately.

## Modlist

This page contains all mods in the position order defined by MO2.
The order cannot be changed (currently not planned) in contrast to MO2 handling the mod sequence shown on the screen.

Each entry presents a single mod but containing only minimal information required for defining the engine.

For example: Mod Name, Engine 1, Engine 2, Engine 3, skse, defined

(defined: The user has defined which engine is supported by the dll)

In addition each entry is marked in different colors.

White: Non-SKSE mod
Green: SKSE mod that was defined by the user
Yellow: SKSE mod that was not defined by the user

Future colors could indicate a mod that could not be identified similar to MO2.

## History

This page shows all modlist.txt file from the backup. Each file can be viewed in list style but nothing more (no marked lines or other editing).

A filter does exist for specific mod types (skse / non skse / non mod)

fyi future feature may allow comparison of the modlist.txt files.

These views will be independent of the main view that can serve as reference for editing the modlist. This idea is platform dependent.

## Backup

This page shows all files in the backup folder. Each file can be viewed in readonly mode.

The page consist of extra action buttons.

New: creates a user backup (in a separate folder). This can be the current modlist or a backed up one.

Use: replaces the current modlist with the one from the backup. User must confirm selection. (The previous modlist will be backed up).

Compare: shows differences to the current modlist (only skse mods, "all" / "skse can be selected to show/hide other mods)

## Technical

The UI is implemented in QT / QML (Pyside6).

The primary platform is PC. Mobile use is possible

The responsibility for correct engine is solely on the user.

The UI does not use Internet / Nexusmods / meta information to get mod information.
(fyi meta data rarely contains information and it's only in description)

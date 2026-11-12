# User Experience - Look and Feel of MOMM

MOMM - MO2 Modlist (Engine) Manager is a tool handling a specific use case: Supported Engine mods. The UI follows
a very different way that aim to be more compatible on all platforms.

The theme of the app is dark. Should the demand be high enough, other
themes can be introduced (via settings / json file). These should contain
settings for markers color, font color, font size, font name, background color

## Top

The entry ideally shows the list of all mods similar to MO2 itself - but without settings or buttons.
This looks similar to mobile apps. A part of the UI there has a possibiltiy to navigate to certain parts.

The Top of the program contains Text or Graphical Buttons to enter specific parts of the app.
Similar to a tool box, but less cluttered (avoiding drop down lists or activation state)

MOMM has four parts: Settings, Main list, Backup, History.
The current part is not shown (so the "entry" shows Settings, Backup, History or correspondent icons)
Long Press on the top element switches between icon and text view (text is default). This setting is stored.

The User should imagine each part as a page.

## Settings

Settings: Modify the Settings file - the UI itself depends on
the Settings structure. It is dynamically created with fixed
properties following json principles.

The top in our case is the list of entries that can be changed.

Editing text entries uses system typical editor.
On-screen-keyboard should not obscure the entry. 
Automatic scrolling should be done in this special case. 
System On-Screen-Keyboard are to be used. 
The app should not try to add extra buttons for "confirmation".

Undo: Currently not planned to add an extra Undo-functionality.
PC-typical "Ctrl-Z" (or correspondant Mobile variants)
should remain enabled. 

This results in a layout where each entry is shown.

Entries are either single values or arrays. They look very similar.

For example "version" is just a text field.
Each entry "storage" is on the same line, so you do not see a tree but

* storage - main csv file
* storage - history directory
* etc. with text fields

game engines are different. Since the screen space is limited, 
we use a listbox where you select the engine.

* The entries are on the right side of the listbox. 
* The entries are updated after selection.

There is no "save" button. Entries are updated as soon as the
user leaves the field or changes a value. 

Validity checks are performed immediately.

Export Folder may not point to MO2 profiles folder. If the user
tries to set it there, the application will return an error.

UI Settings are hidden. (Press on "UI") to show them to show that these
are meant to be set outside settings (and to save space)

If amount of settings is high, a second group should preferred over scrolling.
Group could be displayed at top or bottom (the latter makes it easier to read).

## Main List

This page shows all mods in the position order defined by MO2.
The order cannot be changed (currently not planned).
MO2 in contrast handles the mod sequence shown on the screen.

Each entry presents a single mod but containing only minimal information required for defining the engine.

For example: Mod Name, Engine 1, Engine 2, Engine 3, skse, reviewed

(defined: The user has defined which engine is supported by the dll)

Engines are defines in settings.

Tapping on an engine entry toggles support on/off

User needs to provide information if skse mod supports specific engine.
by default the text "unknown" is used. by tapping/clicking on it, the text is
changed to "supported". Another tap/click changes it to "incompatible".
The text are purposely different for faster visual recognition of the status.
A select box for the state shall not be used.

If information are provided defined is tapped. As long as defined is active, engine information cannot be changed (to prevent accidently editing)
the term "reviewed" shall not be used for a single row, instead the app uses a simple "yes" and "no" text entry.
The Status element can have a reviewed text, if everything was done (else "please review").

In addition each entry is marked in different colors.

1. White: Non-SKSE mod
2. Green: SKSE mod that was defined by the user
3. Yellow: SKSE mod that was not defined by the user
4. Grey: Not a mod (separator)

Future colors could indicate a mod that could not be identified similar to MO2.

The application backends knows if a mod is an skse mod or not.
User cannot change this information. Should a mod change from a
non skse mod into a skse mod (or reversed) the main list needs to
be updated.

The changes are immediately stored into Database / CSV (backend specific).
User can "refresh" the main list. In this case the original modlist from the MO2 folder is merged with the main list.

A successfully merged main list needs to be reviewed again by the user.
skse mods that did not change (same version), remain in state finished.
The backend takes care of version identification.

Should errors occur from Export, Saving, Loading etc. they will be shown on
the lower element of the page. A longpress can hide the report (reduced to one line instead of the last 5).
Tapping on the element opens a page with the messages. In this screen single or all messages can be removed.
Using the clear element shows a warning. Single entries can be deleted using typical system methods like
swiping, double click, double tap, an x button to the right or similar methods.

On top any operation like switching to another page, refresh etc. creates a Snapshot
on top of other operations. The user needs to confirm any operation on his unfinished
main list.

A filter for mod types shall not be used for the time being.

If there are more mods than fit on the page, page numbers should be added,
and navigation with navigation elements like page number, next, previous, next to review.
Scroll bar with scroll bar markers should be avoided for navigation.

There shall not be any statistical information like number of mods that need to be reviewed,
new entries that were added etc. which would cause distraction and stress. This may be added
as a future feature on a separate page or a dialog that can be shown after merging.
These information clutter the screen and take previous space away.

## History

This page shows all modlist.txt file from the backup. Each file can be viewed in list style but nothing more (no marked lines or other editing).

A filter does exist for specific mod types (skse / non skse / non mod)
the filter is activated by tapping on it. the entries have marking colors
similar to the main list:

skse: marked green
non skse: marked white
non mod: marked grey.

As in main list the contrast of the font color must be good enough to read it.

fyi future feature may allow comparison of the modlist.txt files.

These views are independent of the main view that can serve as reference for editing the main list. This idea is platform dependent.

modlist.txt are the backup of the MO2 modlist files, not the main list.

Old main list files need to be loaded to be viewed (see Backup)

There shall not be a comparison from old modlist.txt files with main list. The interface between those
too shall always be merge step. The user is responsible to define clear steps how to use MO2 with this application.

For example he adds or updates 30 mods. Afterwards he updates the csv main list. Ideally he does
not need to export the list. This will only be done after the mod changes are done.

The History is not meant for statistical or review purposes, but only for emergency purposes when something went wrong.

## Backup

This page shows all list files in the backup folder. Each file can be viewed in readonly mode.

The page consist of extra action buttons.

New: creates a user backup (in a separate folder). This can be the current main list or a backed up one.

Use: replaces the current main list with the one from the backup. User must confirm selection. (The previous main list will be backed up).

Compare: shows differences to the current main list (only skse mods, "all" / "skse can be selected to show/hide other mods)

This page does not show the old modlist.txt files from MO2.

The read-only view of the backup is the same as the main list.

Creation of Backups when editing a main list, creates temporary Snapshots.
These are not done for each change, but for a certain amount of finished edits
This amount are steps and by default 5 steps (around 10-20 edits) are necessary
to create a Snapshot. The number of steps can be set in the settings (a warning
should be shown when they are 3 or lower that this will prevent to restore a larger
amount of recent changes.

## Technical

The UI is implemented in QT / QML (Pyside6).

The primary platform is PC. Mobile use is possible

The responsibility for correct engine is solely on the user.

The UI does not use Internet / Nexusmods / meta information to get mod information.
(fyi meta data rarely contains information and it's only in description)

## Extra Notes (for avoiding confusing with backend)

An Overview is purposely left out to keep the application simple.
This would be nothing but an empty page but 4 texts / buttons to in the top element to select.

History on UI side is purposely only for modlist.txt (i.e. MO2 modlist) management.
The idea is that the history contains the source of truth. In the end the
main list is only a representation of various similar modlist files, but nothing
that will be used as it is in MO2. On top simply by exporting the current main list
a modlist.txt can be created and checked in the History page.

Import is purposely held very simple in main list. The main list shall be close to
the source of truth of MO2. The idea is that the user does not use multiple instances
for each engine, but one profile or maybe three. This means that History is limited similary
to what can be done with the backed up modlist.txt files. 

Merging is purposely kept as simple as possible. Using the history can easily cause confusion
thus increasing the danger to destroys parts of the original modlist.txt. This is also the
reason why there is currently no compare functionality in History. The History and the Exported
files are strictly separated because the Exported files are meant to become the new source
of truth. There is a message shown that the Exported files should be compared with the existing
one before overwriting it. The History is an additional backup step to prevent that with accidental
overwrites of modlist.txt in MO2 the old modlist.txt can be restored in case the user forgot to
create the necessary backup before starting a new main list or merging into the existing one.

Configuration of UI is purposely kept as close as possible to the part that should be configured
(with exception of a possible future theme settings). When reading the UI settings, to avoid that
the User is getting confused with a long description or a name that doesn't make him remember where
this UI function is actually used. That's why changes in UI configuration are immediately stored.

Maintenance is done in main list view only. As described the Backup page allows to view old CSV
or Snapshots and compare them. This is done purposely since the view of the main list shall remain
the same even when it is read-only. Currently filtering are the only extra actions from the read-only
view that are meant to find problems in the main list faster. While editing adding a filter has been
disregarded because the modlist sequence is an important part for remembering skse mods depencencies.
Example: some mods overwrite dlls and scripts, a second mod may overwrite other parts. When such a mod
is missing, the user could forget more easily the dependencies and make either mistakes or needs to
switch to MO2 often and having a harder time to find the mods he want to check.

Use cases only explain the necessary operations that the user wants to perform. The background and
reasoning behind it do not belong in the Use Case documentation.

## Mobile UI

The Mobile UI is meant to run in the same aspect-ration as the desktop application.
The primary use for mobile is tablet. Because the amount of phone users is expected to be
low for now the UI should remain as similar as possible. Especially a compact view leaving out
columns due to lack of space and needing a complicated mechanism for editing each entry shall not be done.

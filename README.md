# MO2 Modlist merging tool

MOMM - a tool that allows merging modlists of multiple Skyrim engines.

## Introduction

MOMM allows to merge multiple MO2's modlist.txt under the use of created main modlist csv.

- Read modlist.txt from an MO2 installation (path: settings)
- creates a csv (or an sqlite file should it get slow) for mods
- allows to select which skse mods are 1.5, 1.6, 1.7 (VR indirectly supported)
- does not allow activating or shuffling mods (MO2 remains source of truth)
- merging with other modlist (updates, modlist from other installation)
- handling of partial modlists (recognizing and/or asking the user)
- regulary backups of all your modlist changes done with the tool
- a json file that records the changes ("operations")

This mod is mainly interesting for modlist maintainers that support multiple
Skyrim engines to reduce the amount of maintenance (single modlist instead
of multiple modlist duplication work). The modlist.txt from MO2 is the source
of truth (except for partial modlists).

## Tips

If you use the tool somewhat regulary (depending on how often you have
finished a larger amount of addition, deletions or updates), you will
have an readably overview of the changes you did. With the amount of
updates coming out in 2026 it's easy to forget what you have done as
a modlist maintainer. 

## Requirements

- MO2 installation for Skyrim SE/AE (VR indirectly supported)
- At least one (Default) profile 
- multiple installed Skyrim mods

## Usage

- There is a UI and commandline variant of this tool. The command line
  is currently only used internally for basic on-the-spot backend checks
- UI has three distinctive parts: Settings, Merging, History
- Settings allow you to define Paths and some features of the application
- Merging allows you to automatically or manually load a modlist. Afterwards
  you need to define which engine mods do support which Skyrim engine
- Definition of Skyrim Engines used is done via settings. The application
  cannot find out by itself if a dll supports a specific game engine.
- Maintaining a single "main" list containing both all mods from your mod list
  and all engine mods from your mod list. 
- Limitied amount of merging different mod lists (partial mod lists)
- History allows you to check past changes you have done. The changes
  are all sorted by date. On top you can load the 10 previous changes.
- Exporting of a MO2 modlist. It will not overwrite your MO2 modlist.
  It falls into your responsibility to compare both modlists and copy
  or merge the exported modlist into your modlist.
- Making regular backups of your main MO2 profile you work on is expected.

## Future ideas

- Store more details in history (amount of mods changes, maybe dates)
- Store details about single mods (last change, current version, order change (position))
- Store details about mod files changed (new files, changed files, removed files)
- Allow settings to be changed in application
- Allow engines to be added or removed
- Allow import / export of support "knowledge" (import from sources like modding.wiki is
  not planned; format will be a simplified csv format)
- Allow storing of multiple partial lists (similar to, but different from MO2 profiles).
  this would especially allow filtering mods not used with some modlists because they lack
  API support provided by specific engine mods.

## License

This project and it's code is license under GPL v3.0
The General Modding Excemption applies to this code as well

Project name, application name, assets are excluded from the license.

This generally means for example
a) you can use the code in parts in your application as
you wish as long as your project remains GPL v3.0
b) you can create a similar application under a different name and logo
under the same license
c) you are allowed to use my code for Nexus donation points or similar
forms of donations (incl. patreon) for the portion of extra development
efforts from your side.

## Contact and Contribution

Please contact the team of this project if you have more questions about the project.
Do not hesitate to create issue reports for problems you have
The team is happy for contributions to the project in form of pull requests or
patches submitted via issue requests.

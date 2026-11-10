# MO2 Modlist merging tool for multiple Skyrim engines

## Introduction

Application to merge MO2's modlist.txt with existing created master modlist csv.

- Read modlist.txt from an MO2 installation (path: settings)
- creates a csv (or sql with sqlite if this should get slow) for mods
- allows to select which mods are 1.5, 1.6, 1.7 (VR indirectly supported)
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


## Future ideas

- Store more details in history (amount of mods changes, maybe dates)
- Store details about single mods (last change, current version, order change (position))
- Store details about mod files changed (new files, changed files, removed files)
- Allow settings to be changed in application
- Allow engines to be added or removed
- Allow import / export of support "knowledge" (import from sources like modding.wiki is
  not planned; format will be a simplified csv format)

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

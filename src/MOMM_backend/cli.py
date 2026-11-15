from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_settings, save_settings, AppSettings
from .errors import ModlistManagerError
from .validation import validate_settings


def _default_settings() -> AppSettings:
    return AppSettings.from_dict({
        "version": "1.0",
        "game_engines": [
            {"id": "skyrim-1.5.97", "name": "Skyrim 1.5.97", "version": "1.5.97"},
            {"id": "skyrim-1.6.1170", "name": "Skyrim 1.6.1170", "version": "1.6.1170"},
            {"id": "skyrim-1.7.104", "name": "Skyrim 1.7.104", "version": "1.7.104"}
        ],
        "instances": [],
        "storage": {
            "main_file": "momm-data/modlist_current.csv",
            "history_directory": "momm-data/history",
            "patch_directory": "momm-data/patches",
            "snapshot_directory": "momm-data/snapshots",
            "mo2_profiles_directory": "momm-data/MO2/profiles"
        },
        "backup": {"enabled": True, "keep_snapshots": 10, "preserve_imported_modlists": True},
        "merge": {
            "default_source_scope": "ask",
            "ignore_trailing_disabled_entries": True,
            "require_confirmation": True
        },
        "ui": {"show_incompatible_mods": True, "show_unknown_compatibility": True}
    })

def main() -> int:
    parser = argparse.ArgumentParser(description="MOMM MO2 Modlist Manager — base configuration check")
    parser.add_argument("--settings", default="settings.json", help="Path to settings.json")
    args = parser.parse_args()
    path = Path(args.settings)

    try:
        if not path.exists():
            save_settings(_default_settings(), path)
            print(f"Created default settings: {path}")
        settings = load_settings(path)
        warnings = validate_settings(settings)
    except ModlistManagerError as exc:
        parser.error(str(exc))

    print(f"Settings version: {settings.version}")
    print(f"Configured engines: {len(settings.engines)}")
    for engine in settings.engines.all():
        state = "selectable" if engine.selectable else "retired"
        print(f"  - {engine.name} [{engine.id}] ({state})")
    print(f"MO2 instances: {len(settings.instances)}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    print("Configuration is valid.")
    return 0

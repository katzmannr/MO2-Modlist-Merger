
from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .enums import EntryType
from .history import HistoryManager
from .models import EngineState, MainModlist
from .parser import parse_modlist_file
from .repository import MainRepository


@dataclass(frozen=True, slots=True)
class MO2Profile:
    name: str
    directory: Path
    modlist_path: Path


@dataclass(frozen=True, slots=True)
class ProfileSwitchResult:
    main_list: MainModlist
    backup_path: Path | None
    preserved_mods: int
    source_path: Path


def discover_profiles(directory: str | Path) -> list[MO2Profile]:
    """Discover immediate MO2 profile subdirectories containing modlist.txt."""
    root = Path(directory)

    if not root.exists():
        return []

    if not root.is_dir():
        raise NotADirectoryError(f"MO2 profiles path is not a directory: {root}")

    profiles = []

    for folder in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
        modlist = folder / "modlist.txt"

        if folder.is_dir() and modlist.is_file():
            profiles.append(
                MO2Profile(
                    name=folder.name,
                    directory=folder,
                    modlist_path=modlist,
                )
            )

    return profiles


def carry_forward_knowledge(
    source: MainModlist,
    previous: MainModlist | None,
    engine_ids: tuple[str, ...] | list[str],
) -> tuple[MainModlist, int]:
    """Use the new profile for order and MO2 activation."""
    result = source.clone()

    if previous is None:
        return result, 0

    previous_by_name = {
        entry.name: entry
        for entry in previous.entries
        if entry.entry_type is EntryType.MOD
    }

    preserved = 0

    for entry in result.entries:
        if entry.entry_type is not EntryType.MOD:
            continue

        old_entry = previous_by_name.get(entry.name)

        if old_entry is None:
            continue

        # The profile determines global MO2 activation.
        # The previous list contributes knowledge only.
        entry.has_dll = old_entry.has_dll
        entry.review_status = old_entry.review_status

        compatibility = {}

        for engine_id in engine_ids:
            old_state = old_entry.compatibility.get(
                engine_id,
                EngineState(),
            )

            compatible = old_state.compatible

            # The new profile's activation takes precedence.
            # An incompatible engine remains inactive.
            if not entry.active:
                engine_active = False
            elif compatible is True:
                engine_active = True
            elif compatible is False:
                engine_active = False
            else:
                engine_active = None

            compatibility[engine_id] = EngineState(
                compatible=compatible,
                active=engine_active,
            )

        entry.compatibility = compatibility
        preserved += 1

    return result, preserved


def _restore_file(
    path: Path,
    existed: bool,
    original_bytes: bytes | None,
) -> None:
    if not existed:
        path.unlink(missing_ok=True)
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_suffix(path.suffix + ".rollback.tmp")
    temporary.write_bytes(original_bytes or b"")
    os.replace(temporary, path)


def switch_to_profile(
    profile_file: str | Path,
    previous_main: MainModlist | None,
    repository: MainRepository,
    history: HistoryManager,
) -> ProfileSwitchResult:
    """Replace the current Main List with a selected MO2 profile."""
    source_path = Path(profile_file)

    # Parse first. A malformed profile must never destroy the current list.
    parsed = parse_modlist_file(source_path)

    if repository.main_path.exists() and previous_main is None:
        raise RuntimeError(
            "The existing Main List CSV could not be loaded. "
            "Profile switching was stopped to avoid losing its data."
        )

    new_main, preserved = carry_forward_knowledge(
        parsed.main_list,
        previous_main,
        repository.engine_ids,
    )

    new_main.validate(set(repository.engine_ids))

    main_path = repository.main_path
    workflow_path = repository.workflow_path

    main_existed = main_path.exists()
    workflow_existed = workflow_path.exists()

    main_bytes = main_path.read_bytes() if main_existed else None
    workflow_bytes = workflow_path.read_bytes() if workflow_existed else None

    history.root.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None
    snapshots_existed = history.snapshots.exists()
    snapshots_staged = False

    staging_root = Path(
        tempfile.mkdtemp(
            prefix=".profile-switch-",
            dir=history.root,
        )
    )
    staged_snapshots = staging_root / "snapshots"

    try:
        # Create a permanent backup from the previous in-memory Main List.
        # This is separate from automatic snapshots.
        if previous_main is not None:
            history.backups.mkdir(parents=True, exist_ok=True)

            stamp = datetime.now().astimezone().strftime(
                "%Y-%m-%d_%H%M%S_%f"
            )
            backup_path = history.backups / f"main_{stamp}.csv"

            repository.csv_store.save(previous_main, backup_path)

        # Move the old snapshot directory aside. It can be restored if
        # the CSV or workflow write fails.
        if snapshots_existed:
            os.replace(history.snapshots, staged_snapshots)
            snapshots_staged = True

        # The new list starts a new snapshot lineage.
        history.snapshots.mkdir(parents=True, exist_ok=True)

        # Replace the current CSV and its separate review metadata.
        repository.csv_store.save(new_main, main_path)
        repository.workflow_store.save(workflow_path, new_main)

    except Exception:
        # Restore the previous Main List and workflow metadata.
        _restore_file(main_path, main_existed, main_bytes)
        _restore_file(workflow_path, workflow_existed, workflow_bytes)

        # Restore the old snapshot directory if it was moved.
        if snapshots_staged:
            shutil.rmtree(history.snapshots, ignore_errors=True)
            os.replace(staged_snapshots, history.snapshots)
        elif not snapshots_existed:
            shutil.rmtree(history.snapshots, ignore_errors=True)

        if backup_path is not None:
            backup_path.unlink(missing_ok=True)

        raise

    finally:
        # On success this permanently removes the old snapshot lineage.
        # On failure the snapshots have already been moved back.
        shutil.rmtree(staging_root, ignore_errors=True)

    return ProfileSwitchResult(
        main_list=new_main,
        backup_path=backup_path,
        preserved_mods=preserved,
        source_path=source_path.resolve(),
    )

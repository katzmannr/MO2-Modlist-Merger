from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot

from MOMM_backend.config import load_settings, save_settings
from MOMM_backend.history import HistoryManager
from MOMM_backend.repository import MainRepository
from MOMM_backend.profiles import discover_profiles, switch_to_profile

from MOMM_frontend.main_list_model import MainListModel


class BackendInterface(QObject):
    statusChanged = Signal()
    enginesChanged = Signal()
    settingsChanged = Signal()
    archivesChanged = Signal()
    navigationLabelsChanged = Signal()
    profilesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_list_model = MainListModel(self)

        self._settings = None
        self._repository = None
        self._history = None

        self._status_text = "Starting MOMM"
        self._status_details = ""
        self._engine_list = []
        self._settings_rows = []
        self._history_items = []
        self._backup_items = []
        self._navigation_labels = True

        self._current_main_list = None
        self._profiles = []
        self._selected_profile = ""
        self._profiles_directory = None
        self._settings_path = None
        self._project_root = Path(__file__).resolve().parents[2]

        self._initialize()

    def _initialize(self):
        try:
            project_root = Path(__file__).resolve().parents[2]
            default_settings = (
                project_root / "dist" / "settings" / "settings.json"
            )
            settings_path = Path(
                os.environ.get("MOMM_SETTINGS", str(default_settings))
            )

            self._settings = load_settings(settings_path)

            storage = self._settings.storage
            main_path = Path(
                storage.get("main_file", "momm-data/modlist_main.csv")
            )
            history_path = Path(
                storage.get("history_directory", "momm-data/history")
            )

            engine_ids = self._settings.engines.ids()
            active_ids = self._settings.engines.ids(active_only=True)

            self._history = HistoryManager(
                history_path,
                keep_snapshots=int(
                    self._settings.backup.get("keep_snapshots", 10)
                ),
            )

            self._repository = MainRepository(
                main_path,
                engine_ids,
                active_ids,
                history=self._history,
            )

            self._refresh_profiles()

            self._engine_list = [
                {
                    "id": engine.id,
                    "name": engine.name,
                    "version": engine.version,
                    "status": engine.status.value,
                }
                for engine in self._settings.engines.all()
            ]

            self._navigation_labels = bool(
                self._settings.ui.get("show_navigation_labels", True)
            )

            self._refresh_settings_rows()
            self.refresh_main_list()
            self.refresh_archives()

            settings_path = Path(
                os.environ.get(
                    "MOMM_SETTINGS",
                    str(self._project_root / "dist" / "settings" / "settings.json"),
                )
            )
            self._settings_path = settings_path

            self._settings = load_settings(settings_path)
            storage = self._settings.storage

            def resolve_storage_path(value: str) -> Path:
                path = Path(value)
                return path if path.is_absolute() else self._project_root / path

            main_path = resolve_storage_path(
                storage.get("main_file", "momm-data/modlist_main.csv")
            )
            history_path = resolve_storage_path(
                storage.get("history_directory", "momm-data/history")
            )
            self._profiles_directory = resolve_storage_path(
                storage.get("mo2_profiles_directory", "")
            )

            self._selected_profile = storage.get("selected_profile", "")

        except Exception as exc:
            self._set_status(
                "Application initialization failed",
                str(exc),
            )

    def _set_status(self, summary: str, details: str = ""):
        self._status_text = summary
        self._status_details = details
        self.statusChanged.emit()

    def _refresh_settings_rows(self):
        if self._settings is None:
            self._settings_rows = []
            return

        rows = []
        raw = self._settings.to_dict()

        for group, values in raw.items():
            if group == "ui":
                continue

            if isinstance(values, dict):
                for key, value in values.items():
                    rows.append({
                        "group": group,
                        "label": key,
                        "value": str(value),
                    })
            elif isinstance(values, list):
                rows.append({
                    "group": group,
                    "label": group,
                    "value": str(values),
                })
            else:
                rows.append({
                    "group": "General",
                    "label": group,
                    "value": str(values),
                })

        self._settings_rows = rows
        self.settingsChanged.emit()

    def _refresh_profiles(self):
        if self._profiles_directory is None:
            self._profiles = []
        else:
            try:
                self._profiles = discover_profiles(self._profiles_directory)
            except Exception as exc:
                self._profiles = []
                self._set_status(
                    "Could not discover MO2 profiles",
                    str(exc),
                )

        if self._selected_profile not in {
            profile.name for profile in self._profiles
        }:
            self._selected_profile = ""

        self.profilesChanged.emit()

    @Property("QVariantList", notify=profilesChanged)
    def profileNames(self):
        return [profile.name for profile in self._profiles]

    @Property(str, notify=profilesChanged)
    def selectedProfile(self):
        return self._selected_profile

    @Property(int, notify=profilesChanged)
    def unreviewedSkseCount(self):
        if self._current_main_list is None:
            return 0

        from MOMM_backend.enums import EntryType, ReviewStatus

        return sum(
            1
            for entry in self._current_main_list.entries
            if entry.entry_type is EntryType.MOD
            and entry.has_dll is True
            and entry.review_status is not ReviewStatus.DONE
        )

    @Slot(str)
    def selectProfile(self, profile_name: str):
        if profile_name not in {p.name for p in self._profiles}:
            self._set_status(
                "Unknown MO2 profile",
                profile_name,
            )
            return

        self._selected_profile = profile_name
        self.profilesChanged.emit()

    @Slot(str)
    def loadProfile(self, profile_name: str):
        if self._repository is None or self._history is None:
            self._set_status("Profile loading unavailable")
            return

        profile = next(
            (p for p in self._profiles if p.name == profile_name),
            None,
        )

        if profile is None:
            self._set_status(
                "MO2 profile not found",
                profile_name,
            )
            return

        try:
            result = switch_to_profile(
                profile.modlist_path,
                self._current_main_list,
                self._repository,
                self._history,
            )

            # Update in-memory state only after the backend replacement succeeds.
            self._current_main_list = result.main_list.clone()
            self.main_list_model.set_main_list(result.main_list)

            self._selected_profile = profile.name
            self._settings.storage["selected_profile"] = profile.name

            details = (
                f"Source: {result.source_path}\n"
                f"Known mods carrying forward: {result.preserved_mods}\n"
                f"Previous Main List backup: "
                f"{result.backup_path or 'No previous list'}\n"
                "Previous snapshots were cleared."
            )

            try:
                save_settings(self._settings, self._settings_path)
            except Exception as exc:
                details += f"\nCould not save selected profile setting: {exc}"

            self._refresh_settings_rows()
            self.refresh_archives()
            self.profilesChanged.emit()

            self._set_status(
                f"Loaded MO2 profile: {profile.name}",
                details,
            )

        except Exception as exc:
            self._set_status(
                "Profile switch failed — previous Main List retained",
                str(exc),
            )

    def refresh_main_list(self):
        if self._repository is None:
            self.main_list_model.set_main_list(None)
            return

        result = self._repository.load()

        self._current_main_list = (
            result.main_list.clone()
            if result.success and result.main_list is not None
            else None
        )

        self.main_list_model.set_main_list(result.main_list)

        messages = [
            getattr(issue, "message", str(issue))
            for issue in result.issues
        ]

        if result.main_list is None:
            self._set_status(
                "Main List could not be loaded",
                "\n".join(messages),
            )
        elif messages:
            self._set_status(
                "Main List loaded with diagnostics",
                "\n".join(messages),
            )
        else:
            self._set_status(
                f"Main List loaded: {len(result.main_list.entries)} entries"
            )

    def refresh_archives(self):
        if self._history is None:
            return

        self._history_items = []
        self._backup_items = []

        if self._history.imports.exists():
            for folder in sorted(
                self._history.imports.iterdir(),
                reverse=True,
            ):
                if folder.is_dir():
                    self._history_items.append({
                        "label": folder.name,
                        "path": str(folder),
                    })

        if self._history.snapshots.exists():
            for path in sorted(
                self._history.snapshots.glob("main_*.csv"),
                reverse=True,
            ):
                self._backup_items.append({
                    "label": f"Snapshot — {path.name}",
                    "path": str(path),
                })

        if self._history.backups.exists():
            for path in sorted(
                self._history.backups.glob("main_*.csv"),
                reverse=True,
            ):
                self._backup_items.append({
                    "label": f"Backup — {path.name}",
                    "path": str(path),
                })

        self.archivesChanged.emit()

    @Property(str, notify=statusChanged)
    def statusText(self):
        return self._status_text

    @Property(str, notify=statusChanged)
    def statusDetails(self):
        return self._status_details

    @Property("QVariantList", notify=enginesChanged)
    def engineList(self):
        return self._engine_list

    @Property("QVariantList", notify=settingsChanged)
    def settingsRows(self):
        return self._settings_rows

    @Property("QVariantList", notify=archivesChanged)
    def historyItems(self):
        return self._history_items

    @Property("QVariantList", notify=archivesChanged)
    def backupItems(self):
        return self._backup_items

    @Property(bool, notify=navigationLabelsChanged)
    def navigationLabelsVisible(self):
        return self._navigation_labels

    @Slot()
    def toggleNavigationLabels(self):
        self._navigation_labels = not self._navigation_labels

        if self._settings is not None:
            self._settings.ui["show_navigation_labels"] = (
                self._navigation_labels
            )
            try:
                # Settings are persisted immediately.
                # The actual settings path is resolved during initialization.
                project_root = Path(__file__).resolve().parents[2]
                settings_path = Path(
                    os.environ.get(
                        "MOMM_SETTINGS",
                        str(
                            project_root
                            / "dist"
                            / "settings"
                            / "settings.json"
                        ),
                    )
                )
                save_settings(self._settings, settings_path)
            except Exception as exc:
                self._set_status(
                    "Could not save UI settings",
                    str(exc),
                )

        self.navigationLabelsChanged.emit()

    @Slot()
    def refreshMainList(self):
        self.refresh_main_list()

    @Slot()
    def refreshArchives(self):
        self.refresh_archives()

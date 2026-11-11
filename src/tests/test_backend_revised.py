from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from MOMM_backend.csv_store import MainCSVStore
from MOMM_backend.engines import EngineRegistry, GameEngine
from MOMM_backend.enums import EngineStatus, EntryType, ReviewStatus, SourceScope
from MOMM_backend.errors import ConfigurationError, WorkflowCommitResult, WorkflowIssue
from MOMM_backend.config import AppSettings
from MOMM_backend.history import apply_patch, build_patch
from MOMM_backend.repository import MainRepository
from MOMM_backend.merge import preview_merge
from MOMM_backend.models import EngineState, MainModlist, ModlistEntry
from MOMM_backend.exporter import export_modlist_text
from MOMM_backend.parser import parse_modlist_text, ModlistParseError
from MOMM_backend.workflow import review_summary, unreviewed_skse_mods

ENGINES = ("skyrim-1.5.97", "skyrim-1.6.1170")

class ParserTests(unittest.TestCase):
    def test_mo2_parse_export_roundtrip(self):
        source = parse_modlist_text("# header\n+Base\n+_separator_Core\n+DLL Mod\n-Optional\n")
        self.assertEqual(source.entries[1].entry_type, EntryType.SEPARATOR)
        exported = export_modlist_text(source)
        again = parse_modlist_text(exported)
        self.assertEqual(
            [(e.name, e.entry_type, e.active) for e in source.entries],
            [(e.name, e.entry_type, e.active) for e in again.entries],
        )

    def test_malformed_modlist_line_rejected(self):
        with self.assertRaises(ModlistParseError):
            parse_modlist_text("not-an-entry")


class CSVLoadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "main.csv"
        self.store = MainCSVStore(ENGINES)

    def test_round_trip_persists_compatibility_and_per_engine_active(self):
        main_list = MainModlist([
            ModlistEntry("DLL", active=True, has_dll=True, compatibility={
                ENGINES[0]: EngineState(True, True),
                ENGINES[1]: EngineState(False, False),
            }),
            ModlistEntry("Ordinary", active=False, has_dll=False, compatibility={
                ENGINES[0]: EngineState(None, None),
            }),
            ModlistEntry("_separator_Core", entry_type=EntryType.SEPARATOR),
        ])
        self.store.save(main_list, self.path)
        result = self.store.load(self.path)
        self.assertTrue(result.success)
        self.assertEqual(result.main_list.entries[0].compatibility[ENGINES[0]], EngineState(True, True))
        self.assertEqual(result.main_list.entries[0].compatibility[ENGINES[1]], EngineState(False, False))
        self.assertFalse(result.main_list.entries[1].active)
        self.assertIsNone(result.main_list.entries[2].has_dll)

    def test_missing_file_is_fatal_result_not_exception(self):
        result = self.store.load(Path(self.tmp.name) / "missing.csv")
        self.assertFalse(result.success)
        self.assertIsNone(result.main_list)
        self.assertEqual(result.issues[0].severity, "fatal")

    def test_invalid_header_is_fatal(self):
        self.path.write_text("Name,Active\nA,1\n", encoding="utf-8")
        result = self.store.load(self.path)
        self.assertIsNone(result.main_list)
        self.assertEqual(result.issues[0].severity, "fatal")

    def test_unknown_column_is_fatal_structural_error(self):
        self.path.write_text("Name,Type,Active,unknown_engine\nA,mod,1,1\n", encoding="utf-8")
        result = self.store.load(self.path)
        self.assertIsNone(result.main_list)
        self.assertIn("unknown_engine", result.issues[0].message)

    def test_accumulates_independent_row_errors_and_returns_no_main(self):
        self.path.write_text(
            "Name,Type,HasDLL,Active,skyrim-1.5.97,skyrim-1.5.97_active\n"
            "Good,mod,0,1,1,\n"
            "Bad bool,mod,maybe,1,1,\n"
            "Bad type,separatorx,0,perhaps,,\n"
            "Missing active,mod,0,,1,\n",
            encoding="utf-8",
        )
        result = self.store.load(self.path)
        self.assertIsNone(result.main_list)
        self.assertFalse(result.success)
        self.assertGreaterEqual(len(result.errors), 4)
        self.assertEqual([issue.row for issue in result.errors[:2]], [3, 4])

    def test_late_error_discards_valid_prefix(self):
        self.path.write_text(
            "Name,Type,HasDLL,Active\n" +
            "".join(f"Valid {i},mod,0,1\n" for i in range(100)) +
            "Invalid,mod,maybe,1\n",
            encoding="utf-8",
        )
        result = self.store.load(self.path)
        self.assertIsNone(result.main_list)
        self.assertFalse(result.success)

    def test_error_limit_is_configurable_and_stops_early(self):
        store = MainCSVStore(ENGINES, max_errors=2)
        self.path.write_text(
            "Name,Type,HasDLL,Active,skyrim-1.5.97\n"
            "A,mod,x,maybe,invalid\nB,mod,y,1,1\nC,mod,z,1,1\n",
            encoding="utf-8",
        )
        result = store.load(self.path)
        self.assertIsNone(result.main_list)
        self.assertTrue(result.stopped_early)
        self.assertEqual(len(result.errors), 2)  # threshold counts issues, not rows

    def test_legacy_schema_loads_with_warnings(self):
        self.path.write_text(
            "Name,Type,Active,skyrim-1.5.97\nLegacy,mod,1,1\n",
            encoding="utf-8",
        )
        result = self.store.load(self.path)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.main_list)
        self.assertTrue(result.warnings)
        self.assertIsNone(result.main_list.entries[0].has_dll)
        self.assertEqual(result.main_list.entries[0].compatibility[ENGINES[0]].compatible, True)
        self.assertIsNone(result.main_list.entries[0].compatibility[ENGINES[0]].active)

    def test_duplicate_rows_are_accumulated(self):
        self.path.write_text("Name,Type,Active\nA,mod,1\nA,mod,0\n", encoding="utf-8")
        result = self.store.load(self.path)
        self.assertIsNone(result.main_list)
        self.assertTrue(any("Duplicate" in issue.message for issue in result.errors))


class ActivationMergeTests(unittest.TestCase):
    def test_dll_global_disable_clears_all_engine_active_flags(self):
        main_list = MainModlist([ModlistEntry("DLL", active=True, has_dll=True, compatibility={
            ENGINES[0]: EngineState(True, True), ENGINES[1]: EngineState(False, False),
        })])
        source = MainModlist([ModlistEntry("DLL", active=False)])
        result = preview_merge(main_list, source, scope=SourceScope.PARTIAL, engine_ids=ENGINES)
        entry = result.proposed.entries[0]
        self.assertFalse(entry.active)
        self.assertFalse(entry.compatibility[ENGINES[0]].active)
        self.assertFalse(entry.compatibility[ENGINES[1]].active)

    def test_dll_global_enable_activates_compatible_versions_only(self):
        main_list = MainModlist([ModlistEntry("DLL", active=False, has_dll=True, compatibility={
            ENGINES[0]: EngineState(True, False),
            ENGINES[1]: EngineState(False, True),
            "skyrim-unknown": EngineState(None, None),
        })])
        source = MainModlist([ModlistEntry("DLL", active=True)])
        engine_ids = (*ENGINES, "skyrim-unknown")
        result = preview_merge(main_list, source, scope=SourceScope.PARTIAL, engine_ids=engine_ids)
        entry = result.proposed.entries[0]
        self.assertTrue(entry.active)
        self.assertTrue(entry.compatibility[ENGINES[0]].active)
        self.assertFalse(entry.compatibility[ENGINES[1]].active)
        self.assertIsNone(entry.compatibility["skyrim-unknown"].active)
        self.assertFalse(main_list.entries[0].active)  # inputs remain unchanged

    def test_non_dll_mod_activation_is_not_automatically_changed(self):
        main_list = MainModlist([ModlistEntry("Regular", active=False, has_dll=False)])
        source = MainModlist([ModlistEntry("Regular", active=True)])
        result = preview_merge(main_list, source, scope=SourceScope.PARTIAL, engine_ids=ENGINES)
        self.assertFalse(result.proposed.entries[0].active)


class EngineAndWorkflowTests(unittest.TestCase):
    def test_invalid_engine_settings_are_reported_as_configuration_errors(self):
        with self.assertRaises(ConfigurationError):
            AppSettings.from_dict({
                "version": "1.0",
                "game_engines": [
                    {"id": "same", "name": "A", "version": "1"},
                    {"id": "same", "name": "B", "version": "2"},
                ],
            })

    def test_patch_roundtrip_preserves_nested_engine_state(self):
        before = MainModlist([ModlistEntry("DLL", has_dll=True, compatibility={
            ENGINES[0]: EngineState(True, True), ENGINES[1]: EngineState(False, False),
        })])
        after = MainModlist([ModlistEntry("DLL", active=False, has_dll=True, compatibility={
            ENGINES[0]: EngineState(True, False), ENGINES[1]: EngineState(False, False),
        })])
        patch = build_patch(before, after, ENGINES, reason="test")
        applied = apply_patch(before, patch, ENGINES)
        self.assertEqual(applied.entries[0].compatibility[ENGINES[0]], EngineState(True, False))

    def test_repository_exposes_atomic_load_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "main.csv"
            MainCSVStore(ENGINES).save(MainModlist([ModlistEntry("A")]), path)
            repository = MainRepository(path, ENGINES, ENGINES)
            self.assertTrue(repository.load().success)
            path.write_text("Name,Type,Active\nA,mod,maybe\n", encoding="utf-8")
            failed = repository.load()
            self.assertFalse(failed.success)
            self.assertIsNone(failed.main_list)

    def test_engine_retirement_preserves_definition(self):
        registry = EngineRegistry([GameEngine("e1", "Engine", "1.0")])
        retired = registry.confirm("e1")
        self.assertEqual(retired.status, EngineStatus.COMPATIBLE)
        self.assertEqual(registry.ids(), ("e1",))
        self.assertEqual(registry.ids(active_only=True), ())
        self.assertEqual(registry.activate("e1").status, EngineStatus.ACTIVE)

    def test_all_non_done_review_states_are_unreviewed(self):
        main_list = MainModlist([
            ModlistEntry("A", has_dll=True, review_status=ReviewStatus.UNFINISHED),
            ModlistEntry("B", has_dll=True, review_status=ReviewStatus.IN_PROGRESS),
            ModlistEntry("C", has_dll=True, review_status=ReviewStatus.BLOCKED),
            ModlistEntry("D", has_dll=True, review_status=ReviewStatus.DONE),
        ])
        self.assertEqual(unreviewed_skse_mods(main_list), ["A", "B", "C"])
        self.assertEqual(review_summary(main_list), {"skse_mods": 4, "reviewed": 1, "unreviewed": 3})


class MainRepositoryCommitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.main_path = Path(self.tmp.name) / "main.csv"
        self.repository = MainRepository(self.main_path, ENGINES, ENGINES)
        self.original = MainModlist([ModlistEntry("A")])
        MainCSVStore(ENGINES).save(self.original, self.main_path)

    def test_successful_commit_returns_patch_in_result(self):
        before = self.repository.load().main_list
        after = MainModlist([ModlistEntry("A"), ModlistEntry("B")])

        result = self.repository.commit(before, after, reason="test")

        self.assertIsInstance(result, WorkflowCommitResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.patch)
        self.assertEqual(
            [entry.name for entry in self.repository.load().main_list.entries],
            ["A", "B"],
        )

    def test_invalid_proposed_main_list_returns_workflow_issue(self):
        before = self.repository.load().main_list
        after = MainModlist([
            ModlistEntry("A", compatibility={"not-configured": True}),
        ])

        result = self.repository.commit(before, after, reason="test")

        self.assertFalse(result.success)
        self.assertIsNone(result.patch)
        self.assertEqual(result.issues[0].operation, "validate_proposed_main_list")

    def test_stale_main_revision_returns_workflow_issue(self):
        before = self.repository.load().main_list
        MainCSVStore(ENGINES).save(MainModlist([ModlistEntry("A"), ModlistEntry("External")]), self.main_path)
        after = MainModlist([ModlistEntry("A"), ModlistEntry("B")])

        result = self.repository.commit(before, after, reason="test")

        self.assertFalse(result.success)
        self.assertEqual(result.issues[0].operation, "check_main_revision")

    def test_main_csv_write_failure_is_reported_and_old_file_restored(self):
        before = self.repository.load().main_list
        after = MainModlist([ModlistEntry("A"), ModlistEntry("B")])
        original_bytes = self.main_path.read_bytes()

        with patch.object(self.repository.csv_store, "save", side_effect=OSError("disk full")):
            result = self.repository.commit(before, after, reason="test")

        self.assertFalse(result.success)
        self.assertEqual(result.issues[0].operation, "write_main_csv")
        self.assertEqual(self.main_path.read_bytes(), original_bytes)

    def test_workflow_metadata_write_failure_rolls_back_main_csv(self):
        before = self.repository.load().main_list
        after = MainModlist([ModlistEntry("A"), ModlistEntry("B")])
        original_bytes = self.main_path.read_bytes()

        with patch.object(self.repository.workflow_store, "save", side_effect=OSError("read-only")):
            result = self.repository.commit(before, after, reason="test")

        self.assertFalse(result.success)
        self.assertEqual(result.issues[0].operation, "write_workflow_metadata")
        self.assertEqual(self.main_path.read_bytes(), original_bytes)
        self.assertFalse(self.repository.workflow_path.exists())

    def test_invalid_current_csv_is_returned_as_workflow_issue(self):
        before = self.repository.load().main_list
        self.main_path.write_text("Name,Type,Active\\nA,mod,maybe\\n", encoding="utf-8")
        after = MainModlist([ModlistEntry("A"), ModlistEntry("B")])

        result = self.repository.commit(before, after, reason="test")

        self.assertFalse(result.success)
        self.assertEqual(result.issues[0].operation, "load_current_main_list")
        self.assertIsNotNone(result.issues[0].message)



if __name__ == "__main__":
    unittest.main()

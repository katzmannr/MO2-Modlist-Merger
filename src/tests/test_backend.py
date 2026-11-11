import tempfile
import unittest
from pathlib import Path

from MOMM_backend.csv_store import MainCSVStore
from MOMM_backend.enums import EntryType, ReviewStatus
from MOMM_backend.exporter import export_modlist_text
from MOMM_backend.history import build_patch, apply_patch
from MOMM_backend.merge import SourceScope, infer_effective_boundary, preview_merge
from MOMM_backend.models import EngineState, MainModlist, ModlistEntry
from MOMM_backend.parser import parse_modlist_text, ModlistParseError
from MOMM_backend.workflow import ReviewWorkflowStore, unreviewed_skse_mods

ENGINES = ("skyrim-1.5.97", "skyrim-1.6.1170")

class ParserTests(unittest.TestCase):
    def test_parse_and_export_roundtrip(self):
        text = "# header\n+Base\n+separator_Frameworks\n+SKSE Mod\n-Optional Mod\n"
        parsed = parse_modlist_text(text)
        self.assertEqual(len(parsed.entries), 4)
        self.assertEqual(parsed.entries[1].entry_type, EntryType.MOD)
        self.assertTrue(parsed.entries[2].active)
        self.assertFalse(parsed.entries[3].active)
        output = export_modlist_text(parsed)
        reparsed = parse_modlist_text(output)
        self.assertEqual(
            [(e.name, e.entry_type, e.active) for e in parsed.entries],
            [(e.name, e.entry_type, e.active) for e in reparsed.entries],
        )

    def test_malformed_line_rejected(self):
        with self.assertRaises(ModlistParseError):
            parse_modlist_text("not-an-entry")


class CSVTests(unittest.TestCase):
    def test_csv_roundtrip_dynamic_columns_and_dll(self):
        main_list = MainModlist([
            ModlistEntry("SKSE Mod", active=True, has_dll=True,
                         compatibility={ENGINES[0]: True, ENGINES[1]: None}),
            ModlistEntry("Ordinary Mod", active=False, has_dll=False,
                         compatibility={ENGINES[0]: False, ENGINES[1]: True}),
            ModlistEntry("separator_Core", entry_type=EntryType.SEPARATOR),
        ])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "main.csv"
            store = MainCSVStore(ENGINES)
            store.save(main_list, path)
            loaded = store.load(path)
            self.assertEqual(loaded.main_list.entries[0].has_dll, True)
            self.assertEqual(loaded.main_list.entries[0].compatibility[ENGINES[1]], EngineState(None, None))
            self.assertFalse(loaded.main_list.entries[1].active)
            self.assertIsNone(loaded.main_list.entries[2].has_dll)

    def test_legacy_csv_without_dll_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.csv"
            path.write_text(
                "Name,Type,skyrim-1.5.97,skyrim-1.6.1170,Active\n"
                "Old Mod,mod,1,,1\n", encoding="utf-8"
            )
            loaded = MainCSVStore(ENGINES).load(path)
            self.assertIsNone(loaded.main_list.entries[0].has_dll)
            self.assertTrue(loaded.main_list.entries[0].compatibility[ENGINES[0]])


class WorkflowTests(unittest.TestCase):
    def test_review_metadata_is_separate_from_csv(self):
        main_list = MainModlist([
            ModlistEntry("DLL A", has_dll=True),
            ModlistEntry("DLL B", has_dll=True),
            ModlistEntry("No DLL", has_dll=False),
        ])
        self.assertEqual(unreviewed_skse_mods(main_list), ["DLL A", "DLL B"])
        main_list.entries[0].review_status = ReviewStatus.DONE
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.json"
            store = ReviewWorkflowStore()
            store.save(path, main_list)
            loaded = MainModlist([
                ModlistEntry("DLL A", has_dll=True),
                ModlistEntry("DLL B", has_dll=True),
            ])
            store.load(path, loaded)
            self.assertEqual(loaded.entries[0].review_status, ReviewStatus.DONE)
            self.assertEqual(loaded.entries[1].review_status, ReviewStatus.UNSET)


class MergeTests(unittest.TestCase):
    def test_trailing_disabled_entries_do_not_extend_boundary(self):
        source = parse_modlist_text("+A\n+B\n-C\n-D\n")
        self.assertEqual(infer_effective_boundary(source), 1)

    def test_partial_source_never_creates_removal_candidates(self):
        main_list = parse_modlist_text("+A\n+B\n+C\n")
        source = parse_modlist_text("+A\n+B\n")
        preview = preview_merge(main_list, source, scope=SourceScope.PARTIAL)
        self.assertEqual(preview.missing_candidates, [])
        self.assertEqual(preview.ignored_missing, ["C"])

    def test_ask_scope_is_conservative(self):
        main_list = parse_modlist_text("+A\n+B\n")
        source = parse_modlist_text("+A\n")
        preview = preview_merge(main_list, source, scope=SourceScope.ASK)
        self.assertEqual(preview.missing_candidates, [])
        self.assertTrue(preview.warnings)


class PatchTests(unittest.TestCase):
    def test_patch_roundtrip_and_revision_guard(self):
        before = MainModlist([ModlistEntry("A", compatibility={ENGINES[0]: True})])
        after = MainModlist([
            ModlistEntry("A", active=False, compatibility={ENGINES[0]: False}),
            ModlistEntry("B", compatibility={ENGINES[0]: None}),
        ])
        patch = build_patch(before, after, ENGINES, reason="test")
        applied = apply_patch(before, patch, ENGINES)
        self.assertEqual(
            [(e.name, e.active, e.compatibility) for e in applied.entries],
            [(e.name, e.active, e.compatibility) for e in after.entries],
        )
        with self.assertRaises(ValueError):
            apply_patch(after, patch, ENGINES)


if __name__ == "__main__":
    unittest.main()

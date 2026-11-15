
import tempfile
import unittest
from pathlib import Path

from MOMM_backend.csv_store import MainCSVStore
from MOMM_backend.enums import EntryType, ReviewStatus
from MOMM_backend.history import HistoryManager
from MOMM_backend.models import EngineState, MainModlist, ModlistEntry
from MOMM_backend.profiles import (
    carry_forward_knowledge,
    discover_profiles,
    switch_to_profile,
)
from MOMM_backend.repository import MainRepository

ENGINES = ("skyrim-1.5.97", "skyrim-1.6.1170")


class ProfileDiscoveryTests(unittest.TestCase):
    def test_discovers_only_profiles_with_modlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            (root / "Default").mkdir()
            (root / "Default" / "modlist.txt").write_text(
                "+A\n",
                encoding="utf-8",
            )

            (root / "Testing").mkdir()
            (root / "Testing" / "modlist.txt").write_text(
                "-B\n",
                encoding="utf-8",
            )

            (root / "Incomplete").mkdir()

            profiles = discover_profiles(root)

            self.assertEqual(
                [profile.name for profile in profiles],
                ["Default", "Testing"],
            )


class ProfileKnowledgeTests(unittest.TestCase):
    def test_new_profile_controls_order_and_activation(self):
        previous = MainModlist([
            ModlistEntry(
                "Known DLL",
                active=False,
                has_dll=True,
                compatibility={
                    ENGINES[0]: EngineState(True, False),
                    ENGINES[1]: EngineState(False, False),
                },
                review_status=ReviewStatus.DONE,
            ),
            ModlistEntry("Removed Mod", has_dll=False),
        ])

        source = MainModlist([
            ModlistEntry("New Mod", active=False),
            ModlistEntry("Known DLL", active=True),
        ])

        result, preserved = carry_forward_knowledge(
            source,
            previous,
            ENGINES,
        )

        self.assertEqual(
            [entry.name for entry in result.entries],
            ["New Mod", "Known DLL"],
        )

        known = result.entries[1]

        self.assertTrue(known.active)
        self.assertTrue(known.has_dll)
        self.assertTrue(
            known.compatibility[ENGINES[0]].compatible
        )
        self.assertFalse(
            known.compatibility[ENGINES[1]].compatible
        )
        self.assertTrue(
            known.compatibility[ENGINES[0]].active
        )
        self.assertFalse(
            known.compatibility[ENGINES[1]].active
        )
        self.assertEqual(known.review_status, ReviewStatus.DONE)
        self.assertEqual(preserved, 1)

    def test_unknown_mod_does_not_inherit_unrelated_knowledge(self):
        previous = MainModlist([
            ModlistEntry("Old Mod", has_dll=True),
        ])
        source = MainModlist([
            ModlistEntry("New Mod", active=True),
        ])

        result, preserved = carry_forward_knowledge(
            source,
            previous,
            ENGINES,
        )

        self.assertIsNone(result.entries[0].has_dll)
        self.assertEqual(result.entries[0].compatibility, {})
        self.assertEqual(preserved, 0)


class ProfileSwitchTests(unittest.TestCase):
    def test_switch_backs_up_old_list_and_clears_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            main_path = root / "main.csv"
            history = HistoryManager(root / "history")
            repository = MainRepository(
                main_path,
                ENGINES,
                ENGINES,
                history=history,
            )

            previous = MainModlist([
                ModlistEntry("Known DLL", has_dll=True),
                ModlistEntry("Removed Mod"),
            ])

            repository.csv_store.save(previous, main_path)
            repository.workflow_store.save(
                repository.workflow_path,
                previous,
            )

            history.snapshot(main_path)

            profile_dir = root / "profiles" / "Default"
            profile_dir.mkdir(parents=True)
            profile_file = profile_dir / "modlist.txt"
            profile_file.write_text(
                "-New Mod\n"
                "+Known DLL\n",
                encoding="utf-8",
            )

            result = switch_to_profile(
                profile_file,
                previous,
                repository,
                history,
            )

            self.assertEqual(
                [entry.name for entry in result.main_list.entries],
                ["New Mod", "Known DLL"],
            )

            known = result.main_list.entries[1]
            self.assertTrue(known.active)
            self.assertTrue(known.has_dll)

            self.assertIsNotNone(result.backup_path)
            self.assertTrue(result.backup_path.exists())

            backup = repository.csv_store.load(result.backup_path)
            self.assertEqual(
                [entry.name for entry in backup.main_list.entries],
                ["Known DLL", "Removed Mod"],
            )

            self.assertEqual(
                list(history.snapshots.glob("main_*.csv")),
                [],
            )

            loaded = repository.load()
            self.assertTrue(loaded.success)
            self.assertEqual(
                [entry.name for entry in loaded.main_list.entries],
                ["New Mod", "Known DLL"],
            )


if __name__ == "__main__":
    unittest.main()

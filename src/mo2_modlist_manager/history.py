from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import MasterModlist, entry_to_dict

def master_revision(master: MasterModlist, engine_ids: tuple[str, ...] | list[str]) -> str:
    import csv
    import io
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(master.csv_headers(engine_ids))
    for entry in master.entries:
        writer.writerow(master.to_csv_row(entry, engine_ids))
    return hashlib.sha256(buffer.getvalue().encode("utf-8")).hexdigest()

def build_patch(
    before: MasterModlist,
    after: MasterModlist,
    engine_ids: tuple[str, ...] | list[str],
    *,
    reason: str,
) -> dict[str, Any]:
    old_map = {(e.entry_type.value, e.name): entry_to_dict(e, include_review=False) for e in before.entries}
    new_map = {(e.entry_type.value, e.name): entry_to_dict(e, include_review=False) for e in after.entries}
    operations = []
    for key, old_data in old_map.items():
        if key not in new_map:
            operations.append({"operation": "remove_entry", "key": list(key), "old": old_data})
        elif old_data != new_map[key]:
            operations.append({"operation": "update_entry", "key": list(key), "old": old_data, "new": new_map[key]})
    for key, new_data in new_map.items():
        if key not in old_map:
            operations.append({"operation": "add_entry", "key": list(key), "new": new_data})

    old_order = [list((e.entry_type.value, e.name)) for e in before.entries]
    new_order = [list((e.entry_type.value, e.name)) for e in after.entries]
    if old_order != new_order:
        operations.append({"operation": "reorder_entries", "old": old_order, "new": new_order})

    return {
        "schema_version": 1,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reason": reason,
        "expected_revision": master_revision(before, engine_ids),
        "result_revision": master_revision(after, engine_ids),
        "operations": operations,
    }

def apply_patch(master: MasterModlist, patch: dict[str, Any], engine_ids) -> MasterModlist:
    current_revision = master_revision(master, engine_ids)
    if current_revision != patch.get("expected_revision"):
        raise ValueError(
            "Patch revision mismatch: patch expects a different master state."
        )
    by_key = {
        (e.entry_type.value, e.name): entry_to_dict(e)
        for e in master.entries
    }
    for operation in patch.get("operations", []):
        op = operation["operation"]
        if op == "remove_entry":
            by_key.pop(tuple(operation["key"]), None)
        elif op in {"add_entry", "update_entry"}:
            data = operation["new"]
            by_key[tuple(operation["key"])] = data
        elif op == "reorder_entries":
            order = [tuple(k) for k in operation["new"]]
            reordered = [by_key.pop(key) for key in order if key in by_key]
            reordered.extend(by_key.values())
            by_key = {(d["entry_type"], d["name"]): d for d in reordered}
        else:
            raise ValueError(f"Unknown patch operation: {op!r}")
    result = MasterModlist([
        __import__("mo2_modlist_manager.models", fromlist=["entry_from_dict"]).entry_from_dict(v)
        for v in by_key.values()
    ])
    result.validate(set(engine_ids))
    if master_revision(result, engine_ids) != patch.get("result_revision"):
        raise ValueError("Patch result revision does not match its recorded result.")
    return result

class HistoryManager:
    def __init__(self, root: str | Path, keep_snapshots: int = 10):
        self.root = Path(root)
        self.keep_snapshots = max(1, int(keep_snapshots))
        self.imports = self.root / "imports"
        self.snapshots = self.root / "snapshots"
        self.patches = self.root.parent / "patches"

    def archive_import(self, source_file: str | Path, parsed_csv: str, changes: dict) -> Path:
        source = Path(source_file)
        stamp = datetime.now().astimezone().strftime("%Y-%m-%d_%H%M%S_%f")
        destination = self.imports / stamp
        destination.mkdir(parents=True, exist_ok=False)
        shutil.copy2(source, destination / "modlist.txt")
        (destination / "source.csv").write_text(parsed_csv, encoding="utf-8")
        (destination / "changes.json").write_text(
            json.dumps(changes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return destination

    def write_patch(self, patch: dict[str, Any]) -> Path:
        self.patches.mkdir(parents=True, exist_ok=True)
        existing = sorted(self.patches.glob("*.json"))
        number = (int(existing[-1].stem) + 1) if existing and existing[-1].stem.isdigit() else 1
        destination = self.patches / f"{number:04d}.json"
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(patch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(destination)
        return destination

    def snapshot(self, master_csv: str | Path, *, baseline: bool = False) -> Path:
        source = Path(master_csv)
        self.snapshots.mkdir(parents=True, exist_ok=True)
        stamp = "baseline" if baseline else datetime.now().astimezone().strftime("%Y-%m-%d_%H%M%S_%f")
        destination = self.snapshots / f"master_{stamp}.csv"
        shutil.copy2(source, destination)
        self._prune_snapshots()
        return destination

    def _prune_snapshots(self) -> None:
        snapshots = sorted(
            p for p in self.snapshots.glob("master_*.csv") if p.name != "master_baseline.csv"
        )
        for obsolete in snapshots[:-self.keep_snapshots]:
            obsolete.unlink(missing_ok=True)

"""Persistence for review markers, separate from the main CSV."""

from __future__ import annotations

import json
from pathlib import Path

from .enums import EntryType, ReviewStatus
from .models import MainModlist


class ReviewWorkflowStore:
    def load(self, path: str | Path, main_list: MainModlist) -> None:
        source = Path(path)
        if not source.exists():
            return
        data = json.loads(source.read_text(encoding="utf-8"))
        if data.get("version") != 1:
            raise ValueError(f"Unsupported workflow metadata version: {data.get('version')!r}")
        statuses = {
            (item["entry_type"], item["name"]): ReviewStatus(item["status"])
            for item in data.get("reviews", [])
        }
        for entry in main_list.entries:
            if entry.entry_type is EntryType.MOD:
                entry.review_status = statuses.get((entry.entry_type.value, entry.name), ReviewStatus.UNSET)

    def save(self, path: str | Path, main_list: MainModlist) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "reviews": [
                {"entry_type": entry.entry_type.value, "name": entry.name, "status": entry.review_status.value}
                for entry in main_list.entries
                if entry.entry_type is EntryType.MOD and entry.review_status is not ReviewStatus.UNSET
            ],
        }
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(destination)


def unreviewed_skse_mods(main_list: MainModlist) -> list[str]:
    return [
        entry.name for entry in main_list.entries
        if entry.entry_type is EntryType.MOD
        and entry.has_dll is True
        and entry.review_status is not ReviewStatus.DONE
    ]


def review_summary(main_list: MainModlist) -> dict[str, int]:
    dll_mods = [entry for entry in main_list.entries if entry.entry_type is EntryType.MOD and entry.has_dll is True]
    return {
        "skse_mods": len(dll_mods),
        "reviewed": sum(entry.review_status is ReviewStatus.DONE for entry in dll_mods),
        "unreviewed": sum(entry.review_status is not ReviewStatus.DONE for entry in dll_mods),
    }

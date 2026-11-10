from __future__ import annotations

import json
from pathlib import Path

from .enums import EntryType, ReviewStatus
from .models import MasterModlist


class ReviewWorkflowStore:
    """Persistence for UI work markers."""

    def load(self, path: str | Path, master: MasterModlist) -> None:
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
        for entry in master.entries:
            if entry.entry_type is EntryType.MOD:
                entry.review_status = statuses.get(
                    (entry.entry_type.value, entry.name), ReviewStatus.UNSET
                )

    def save(self, path: str | Path, master: MasterModlist) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "reviews": [
                {"entry_type": entry.entry_type.value, "name": entry.name,
                 "status": entry.review_status.value}
                for entry in master.entries
                if entry.entry_type is EntryType.MOD
                and entry.review_status is not ReviewStatus.UNSET
            ],
        }
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(path)


def unreviewed_skse_mods(master: MasterModlist) -> list[str]:
    return [
        entry.name for entry in master.entries
        if entry.entry_type is EntryType.MOD
        and entry.has_dll is True
        and entry.review_status is ReviewStatus.UNSET
    ]


def review_summary(master: MasterModlist) -> dict[str, int]:
    skse = [
        e for e in master.entries
        if e.entry_type is EntryType.MOD and e.has_dll is True
    ]
    return {
        "skse_mods": len(skse),
        "reviewed": sum(e.review_status is ReviewStatus.DONE for e in skse),
        "unreviewed": sum(e.review_status is ReviewStatus.UNSET for e in skse),
    }

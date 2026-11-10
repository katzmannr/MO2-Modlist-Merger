from __future__ import annotations

import csv
from pathlib import Path

from .enums import EntryType
from .errors import ModlistManagerError, ModelValidationError
from .models import MasterModlist, ModlistEntry


class CSVStoreError(ModlistManagerError):
    pass

def _parse_bool(value: str, *, field: str, row_number: int, allow_empty: bool = False):
    normalized = value.strip().lower()
    if allow_empty and normalized == "":
        return None
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    raise CSVStoreError(f"CSV has invalid {field} value {value!r} on row {row_number}.")

class MasterCSVStore:
    """CSV persistence for master data. Review workflow is deliberately separate."""

    def __init__(self, engine_ids: list[str] | tuple[str, ...]):
        self.engine_ids = tuple(engine_ids)

    def load(self, path: str | Path) -> MasterModlist:
        path = Path(path)
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    raise CSVStoreError("Master CSV has no header.")
                required = {"Name", "Type"}
                missing = required - set(reader.fieldnames)
                if missing:
                    raise CSVStoreError(f"Master CSV is missing columns: {sorted(missing)}")
                rows = list(reader)
        except OSError as exc:
            raise CSVStoreError(f"Cannot read master CSV {path}: {exc}") from exc

        entries: list[ModlistEntry] = []
        for row_number, row in enumerate(rows, start=2):
            name = row.get("Name") or ""
            try:
                entry_type = EntryType((row.get("Type") or "mod").strip().lower())
            except ValueError as exc:
                raise CSVStoreError(f"Unknown Type on CSV row {row_number}.") from exc

            if entry_type is EntryType.SEPARATOR:
                entries.append(ModlistEntry(name=name, entry_type=EntryType.SEPARATOR))
                continue

            has_dll = _parse_bool(
                row.get("HasDLL") or "", field="HasDLL", row_number=row_number, allow_empty=True
            )
            compatibility = {}
            for engine_id in self.engine_ids:
                if engine_id in row:
                    compatibility[engine_id]["compatible"] = _parse_bool(
                        row.get(engine_id) or "", field=engine_id,
                        row_number=row_number, allow_empty=True
                    )
                    compatibility[engine_id]["active"] = _parse_bool(
                        row.get(engine_id+"_active") or "", field=engine_id+"_active",
                        row_number=row_number, allow_empty=True
                    )
                else:
                    compatibility[engine_id]["compatible"] = None
                    compatibility[engine_id]["active"] = "0"
            entries.append(ModlistEntry(
                name=name, entry_type=entry_type,
                has_dll=has_dll, compatibility=compatibility
            ))

        master = MasterModlist(entries)
        try:
            master.validate(set(self.engine_ids))
        except ModelValidationError as exc:
            raise CSVStoreError(str(exc)) from exc
        return master

    def save(self, master: MasterModlist, path: str | Path) -> None:
        path = Path(path)
        master.validate(set(self.engine_ids))
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(master.csv_headers(self.engine_ids))
                for entry in master.entries:
                    writer.writerow(master.to_csv_row(entry, self.engine_ids))
            temporary.replace(path)
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            raise CSVStoreError(f"Cannot write master CSV {path}: {exc}") from exc

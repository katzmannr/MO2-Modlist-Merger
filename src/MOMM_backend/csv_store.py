"""Transactional, error-tolerant CSV import and atomic main CSV persistence."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

from .enums import EntryType
from .errors import (
    CSVLoadResult,
    CSVStoreError,
    CSVIssue,
    ModelValidationError,
)
from .models import EngineState, MainModlist, ModlistEntry

_FIXED_COLUMNS = {"Name", "Type", "HasDLL", "Active"}

def _format_bool(value: bool | None) -> str:
    if value is None:
        return ""
    if not isinstance(value, bool):
        raise CSVStoreError(f"Cannot write non-boolean CSV state: {value!r}.")
    return "1" if value else "0"

def _parse_bool(value: str | None,*,row: int,column: str,issues: list[CSVIssue],required: bool = False) -> bool | None:
    """Parse a CSV boolean; append a structured issue rather than raising."""
    normalized = (value or "").strip().lower()
    if not normalized:
        if required:
            issues.append(CSVIssue(row, column, "Missing required value."))
        return None
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    issues.append(CSVIssue(
        row,
        column,
        f"Invalid boolean value: {value!r}. Expected 1, 0 / true, false / yes, no.",
    ))
    return None


class MainCSVStore:
    """Stateless CSV persistence service."""

    # ToDo: Make this part of settings
    MAX_ERRORS = 25

    def __init__(self,engine_ids: list[str] | tuple[str, ...],*,max_errors: int = MAX_ERRORS) -> None:
        ids = tuple(engine_ids)
        if any(not isinstance(item, str) or not item.strip() or item != item.strip() for item in ids):
            raise CSVStoreError("Engine IDs must contain strings without surrounding whitespace.")
        if len(set(ids)) != len(ids):
            raise CSVStoreError("Engine IDs must be unique.")
        if not isinstance(max_errors, int) or isinstance(max_errors, bool) or max_errors < 1:
            raise ValueError("max_errors must be a positive number.")

        engine_columns = [column for engine_id in ids for column in (engine_id, f"{engine_id}_active")]
        all_columns = [*_FIXED_COLUMNS, *engine_columns]
        if len(set(all_columns)) != len(all_columns):
            raise CSVStoreError("Engine IDs generate colliding or reserved CSV column names.")

        self.engine_ids = ids
        self.max_errors = max_errors
        self._headers = MainModlist.csv_headers(ids)

    def load(self, path: str | Path) -> CSVLoadResult:
        source = Path(path)
        issues: list[CSVIssue] = []
        entries: list[ModlistEntry] = []
        seen: set[tuple[EntryType, str]] = set()

        try:
            with source.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                header_issue = self._validate_header(reader.fieldnames)
                if header_issue is not None:
                    return CSVLoadResult(None, [header_issue])

                fieldnames = list(reader.fieldnames or [])
                # One trailing empty header cell is a known hand-edited legacy quirk.
                if fieldnames and fieldnames[-1] == "":
                    fieldnames.pop()
                    reader.fieldnames = fieldnames
                    issues.append(CSVIssue(
                        None, None,
                        "Ignored one empty trailing header column from a legacy CSV.",
                        "warning",
                    ))

                if "HasDLL" not in fieldnames:
                    issues.append(CSVIssue(
                        None, "HasDLL",
                        "Legacy CSV has no HasDLL column; DLL classification will be unknown.",
                        "warning",
                    ))
                for engine_id in self.engine_ids:
                    if engine_id in fieldnames and f"{engine_id}_active" not in fieldnames:
                        issues.append(CSVIssue(
                            None, f"{engine_id}_active",
                            "Legacy CSV has no per-engine activation column; its value will be unknown.",
                            "warning",
                        ))

                try:
                    for row_number, row in enumerate(reader, start=2):
                        if self._is_blank_row(row):
                            continue
                        row_issues: list[CSVIssue] = []
                        extra_values = row.get(None)
                        if extra_values and any(str(value).strip() for value in extra_values):
                            row_issues.append(CSVIssue(
                                row_number, None,
                                "Row contains more values than the header defines.",
                            ))

                        entry = self._parse_row(row, row_number, fieldnames, row_issues)
                        if entry is not None and not row_issues:
                            identity = (entry.entry_type, entry.name)
                            if identity in seen:
                                row_issues.append(CSVIssue(
                                    row_number, "Name",
                                    f"Duplicate {entry.entry_type.value} name: {entry.name!r}.",
                                ))
                            else:
                                seen.add(identity)

                        if row_issues:
                            issues.extend(row_issues)
                        elif entry is not None:
                            entries.append(entry)

                        if self._error_count(issues) >= self.max_errors:
                            warnings = [issue for issue in issues if issue.severity == "warning"]
                            errors = [issue for issue in issues if issue.severity in {"fatal", "error"}]
                            return CSVLoadResult(
                                None,
                                warnings + errors[:self.max_errors],
                                stopped_early=True,
                            )
                except csv.Error as exc:
                    issues.append(CSVIssue(None, None, f"CSV syntax error: {exc}.", "fatal"))
                    return CSVLoadResult(None, issues, stopped_early=True)

        except (OSError, UnicodeError, csv.Error) as exc:
            return CSVLoadResult(
                None,
                [CSVIssue(None, None, f"Cannot read main CSV {source}: {exc}.", "fatal")],
            )

        if self._error_count(issues):
            return CSVLoadResult(None, issues)

        main_list = MainModlist(entries)
        try:
            main_list.validate(set(self.engine_ids))
        except ModelValidationError as exc:
            return CSVLoadResult(None, [CSVIssue(None, None, str(exc), "error")])

        return CSVLoadResult(main_list, issues)

    def _validate_header(self, fieldnames: list[str] | None) -> CSVIssue | None:
        if not fieldnames:
            return CSVIssue(None, None, "Main CSV has no header.", "fatal")

        normalized = list(fieldnames)
        if normalized[-1] == "":
            normalized.pop()
        if any(name is None or not str(name).strip() for name in normalized):
            return CSVIssue(None, None, "Main CSV contains an empty column name.", "fatal")
        if len(normalized) != len(set(normalized)):
            return CSVIssue(None, None, "Main CSV contains duplicate column names.", "fatal")

        missing = {"Name", "Type", "Active"} - set(normalized)
        if missing:
            return CSVIssue(
                None, None, f"Main CSV is missing required columns: {', '.join(sorted(missing))}.",
                "fatal",
            )

        allowed = set(_FIXED_COLUMNS)
        for engine_id in self.engine_ids:
            allowed.update((engine_id, f"{engine_id}_active"))
        unknown = set(normalized) - allowed
        if unknown:
            return CSVIssue(
                None, None,
                "Main CSV contains unknown columns: " + ", ".join(sorted(unknown)) + ".",
                "fatal",
            )
        return None

    @staticmethod
    def _is_blank_row(row: dict) -> bool:
        return all(value is None or not str(value).strip() for value in row.values())

    @staticmethod
    def _error_count(issues: list[CSVIssue]) -> int:
        return sum(issue.severity in {"fatal", "error"} for issue in issues)

    def _parse_row(
        self,
        row: dict[str | None, object],
        row_number: int,
        fieldnames: list[str],
        issues: list[CSVIssue],
    ) -> ModlistEntry | None:
        name = row.get("Name")
        if not isinstance(name, str) or not name.strip():
            issues.append(CSVIssue(row_number, "Name", "Missing required mod/separator name."))
            name = ""
        # Keep the exact stored mod name; only use strip() to detect blank names.

        raw_type = row.get("Type")
        try:
            entry_type = EntryType(str(raw_type or "").strip().lower())
        except ValueError:
            issues.append(CSVIssue(row_number, "Type", f"Unknown entry type: {raw_type!r}."))
            entry_type = None

        if entry_type is EntryType.SEPARATOR:
            # Separators have no activation, DLL classification or engine state.
            for column in ("HasDLL", "Active", *self._engine_columns_present(fieldnames)):
                value = row.get(column)
                if value is not None and str(value).strip():
                    issues.append(CSVIssue(
                        row_number, column,
                        "Separator rows must leave mod-specific fields empty.",
                    ))
            if issues:
                return None
            try:
                return ModlistEntry(name=name, entry_type=EntryType.SEPARATOR)
            except ModelValidationError as exc:
                issues.append(CSVIssue(row_number, "Name", str(exc)))
                return None

        active = _parse_bool(
            row.get("Active") if isinstance(row.get("Active"), str) else None,
            row=row_number, column="Active", issues=issues, required=True,
        )
        has_dll = _parse_bool(
            row.get("HasDLL") if isinstance(row.get("HasDLL"), str) else None,
            row=row_number, column="HasDLL", issues=issues,
        )

        states: dict[str, EngineState] = {}
        for engine_id in self.engine_ids:
            compatible = _parse_bool(
                row.get(engine_id) if isinstance(row.get(engine_id), str) else None,
                row=row_number, column=engine_id, issues=issues,
            ) if engine_id in fieldnames else None
            active_column = f"{engine_id}_active"
            engine_active = _parse_bool(
                row.get(active_column) if isinstance(row.get(active_column), str) else None,
                row=row_number, column=active_column, issues=issues,
            ) if active_column in fieldnames else None
            states[engine_id] = EngineState(compatible, engine_active)

        if entry_type is None or issues:
            return None
        try:
            return ModlistEntry(
                name=name,
                entry_type=entry_type,
                active=active,
                has_dll=has_dll,
                compatibility=states,
            )
        except (ModelValidationError, TypeError, ValueError) as exc:
            issues.append(CSVIssue(row_number, None, f"Invalid model data: {exc}."))
            return None

    @staticmethod
    def _engine_columns_present(fieldnames: list[str]) -> tuple[str, ...]:
        # The caller has already validated all column names.
        return tuple(name for name in fieldnames if name not in _FIXED_COLUMNS)

    def save(self, main_list: MainModlist, path: str | Path) -> None:
        destination = Path(path)
        try:
            main_list.validate(set(self.engine_ids))
        except ModelValidationError as exc:
            raise CSVStoreError(f"Cannot save invalid main list data: {exc}.") from exc

        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="", dir=destination.parent,
                prefix=f".{destination.name}.", suffix=".tmp", delete=False,
            ) as handle:
                temporary_path = handle.name
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(self._headers)
                for entry in main_list.entries:
                    writer.writerow(MainModlist.to_csv_row(entry, self.engine_ids))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, destination)
            temporary_path = None
        except OSError as exc:
            raise CSVStoreError(f"Cannot write main CSV {destination}: {exc}.") from exc
        finally:
            if temporary_path is not None:
                try:
                    os.unlink(temporary_path)
                except FileNotFoundError:
                    pass

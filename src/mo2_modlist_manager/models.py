from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

from .enums import EntryType, ReviewStatus
from .errors import ModelValidationError

CompatibilityValue: TypeAlias = bool | None

@dataclass
class EngineState:
    compatible: bool | None
    active: bool | False

@dataclass(slots=True)
class ModlistEntry:
    """A mod or MO2 separator. List position is represented by collection order."""

    name: str
    entry_type: EntryType = EntryType.MOD
    # Used for non-DLL mods
    active: bool | None = False
    hasdll: bool | None = None
    # Used for engine-specific compatibility and DLL activation
    compatibility: dict[str, EngineState] = field(default_factory=dict)
    review_status: ReviewStatus = ReviewStatus.UNSET

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ModelValidationError("Entry name must be a non-empty string.")
        if self.entry_type is EntryType.SEPARATOR:
            self.active = None
            self.has_dll = None
            self.compatibility.clear()
            self.review_status = ReviewStatus.UNSET
        elif self.active is None:
            raise ModelValidationError("A regular mod must have an activation state.")
        if self.has_dll is not None and not isinstance(self.has_dll, bool):
            raise ModelValidationError("has_dll must be true, false, or None.")
        if not isinstance(self.review_status, ReviewStatus):
            self.review_status = ReviewStatus(self.review_status)
        self._validate_compatibility_values()

    @property
    def is_skse(self) -> bool:
        return self.has_dll is True

    def set_compatibility(self, engine_id: str, value: CompatibilityValue) -> None:
        if self.entry_type is EntryType.SEPARATOR:
            raise ModelValidationError("Separators cannot have compatibility values.")
        if not engine_id:
            raise ModelValidationError("Engine ID must not be empty.")
        if value is not None and not isinstance(value, bool):
            raise ModelValidationError("Compatibility must be true, false, or None.")
        self.compatibility[engine_id] = value

    def _validate_compatibility_values(self) -> None:
        for engine_id, value in self.compatibility.items():
            if not isinstance(engine_id, str) or not engine_id:
                raise ModelValidationError("Compatibility keys must be non-empty engine IDs.")
            if value is not None and not isinstance(value, bool):
                raise ModelValidationError(
                    f"Compatibility for {engine_id!r} must be true, false, or unknown (None)."
                )


@dataclass(slots=True)
class MasterModlist:
    entries: list[ModlistEntry] = field(default_factory=list)

    def validate(self, known_engine_ids: set[str] | None = None) -> None:
        seen: set[tuple[EntryType, str]] = set()
        for index, entry in enumerate(self.entries):
            if not isinstance(entry, ModlistEntry):
                raise ModelValidationError(f"Entry at position {index} is not a ModlistEntry.")
            identity = (entry.entry_type, entry.name)
            if identity in seen:
                raise ModelValidationError(
                    f"Duplicate {entry.entry_type.value} name at position {index}: {entry.name!r}"
                )
            seen.add(identity)
            if entry.entry_type is EntryType.SEPARATOR and (
                entry.active is not None or entry.compatibility or entry.has_dll is not None
            ):
                raise ModelValidationError(f"Separator at position {index} has mod-only fields.")
            if known_engine_ids is not None:
                unknown = set(entry.compatibility) - known_engine_ids
                if unknown:
                    raise ModelValidationError(
                        f"Entry {entry.name!r} references unregistered engines: {sorted(unknown)}"
                    )

    def csv_headers(self, engine_ids: list[str] | tuple[str, ...]) -> list[str]:
        return ["Name", "Type", "Active", "HasDLL", *engine_ids]

    def to_csv_row(self, entry: ModlistEntry, engine_ids: list[str] | tuple[str, ...]) -> list[str]:
        if entry.entry_type is EntryType.SEPARATOR:
            return [entry.name, "separator", "", *("" for _ in engine_ids), ""]
        dll = "" if entry.has_dll is None else ("1" if entry.has_dll else "0")
        values = [
            "" if entry.compatibility.get(engine_id) is None
            else ("1" if entry.compatibility[engine_id] else "0")
            for engine_id in engine_ids
        ]
        return [entry.name, "mod", "1" if entry.active else "0", dll, *values]

    def clone(self) -> "MasterModlist":
        return MasterModlist([entry_from_dict(entry_to_dict(e)) for e in self.entries])


def entry_to_dict(entry: ModlistEntry, *, include_review: bool = True) -> dict:
    result = {
        "name": entry.name,
        "entry_type": entry.entry_type.value,
        "active": entry.active,
        "has_dll": entry.has_dll,
        "compatibility": dict(entry.compatibility),
    }
    if include_review:
        result["review_status"] = entry.review_status.value
    return result


def entry_from_dict(data: dict) -> ModlistEntry:
    return ModlistEntry(
        name=data["name"],
        entry_type=EntryType(data.get("entry_type", "mod")),
        active=data.get("active", False),
        has_dll=data.get("has_dll"),
        compatibility=dict(data.get("compatibility", {})),
        review_status=ReviewStatus(data.get("review_status", "unset")),
    )

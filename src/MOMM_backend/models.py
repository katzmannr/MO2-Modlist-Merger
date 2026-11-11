"""Core MOMM models. List order is the sole source of entry position."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeAlias

from .enums import EntryType, ReviewStatus
from .errors import ModelValidationError

CompatibilityValue: TypeAlias = bool | None

def _require_bool_or_none(value: object, field_name: str) -> None:
    if value is not None and not isinstance(value, bool):
        raise ModelValidationError(f"{field_name} must be true, false, or unknown (None).")


@dataclass(slots=True)
class EngineState:
    """Per-engine compatibility and activation."""

    compatible: CompatibilityValue = None
    active: bool | None = None

    def __post_init__(self) -> None:
        _require_bool_or_none(self.compatible, "EngineState.compatible")
        _require_bool_or_none(self.active, "EngineState.active")

    def clone(self) -> "EngineState":
        return EngineState(self.compatible, self.active)


def _coerce_engine_state(value: EngineState | dict[str, Any] | bool | None) -> EngineState:
    """Normalize the canonical object and the former flat compatibility format."""
    if isinstance(value, EngineState):
        return value.clone()
    if isinstance(value, dict):
        return EngineState(value.get("compatible"), value.get("active"))
    _require_bool_or_none(value, "compatibility value")
    return EngineState(compatible=value)


@dataclass(slots=True)
class ModlistEntry:
    name: str
    entry_type: EntryType = EntryType.MOD
    # The activation state imported from an MO2 modlist.txt.
    active: bool | None = False
    # True = contains SKSE DLL(s), False = no SKSE DLLs, None = not classified.
    has_dll: bool | None = None
    # engine ID -> EngineState(compatibility, DLL-version activation)
    compatibility: dict[str, EngineState | bool | None] = field(default_factory=dict)
    review_status: ReviewStatus = ReviewStatus.UNSET

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ModelValidationError("Entry name must be a valid string.")
        if not isinstance(self.entry_type, EntryType):
            try:
                self.entry_type = EntryType(self.entry_type)
            except (TypeError, ValueError) as exc:
                raise ModelValidationError(f"Invalid entry type: {self.entry_type!r}.") from exc

        if self.entry_type is EntryType.SEPARATOR:
            self.active = None
            self.has_dll = None
            self.compatibility = {}
            self.review_status = ReviewStatus.UNSET
            return

        if not isinstance(self.active, bool):
            raise ModelValidationError("A regular mod must have a boolean MO2 activation state.")
        _require_bool_or_none(self.has_dll, "has_dll")

        if not isinstance(self.review_status, ReviewStatus):
            try:
                self.review_status = ReviewStatus(self.review_status)
            except (TypeError, ValueError) as exc:
                raise ModelValidationError(f"Invalid review status: {self.review_status!r}.") from exc

        normalized: dict[str, EngineState] = {}
        for engine_id, state in self.compatibility.items():
            if not isinstance(engine_id, str) or not engine_id.strip():
                raise ModelValidationError("Compatibility keys must be non-empty engine IDs.")
            normalized[engine_id] = _coerce_engine_state(state)
        self.compatibility = normalized

    @property
    def is_skse(self) -> bool | None:
        return self.has_dll

    def set_compatibility(self, engine_id: str, value: CompatibilityValue) -> None:
        self._check_engine_id(engine_id)
        _require_bool_or_none(value, "compatibility")
        current = self.compatibility.get(engine_id, EngineState())
        self.compatibility[engine_id] = EngineState(value, current.active)

    def set_engine_active(self, engine_id: str, value: bool | None) -> None:
        self._check_engine_id(engine_id)
        _require_bool_or_none(value, "engine activation")
        current = self.compatibility.get(engine_id, EngineState())
        self.compatibility[engine_id] = EngineState(current.compatible, value)

    @staticmethod
    def _check_engine_id(engine_id: str) -> None:
        if not isinstance(engine_id, str) or not engine_id.strip():
            raise ModelValidationError("Engine ID must be a non-empty string.")

    def clone(self) -> "ModlistEntry":
        return ModlistEntry(
            name=self.name,
            entry_type=self.entry_type,
            active=self.active,
            has_dll=self.has_dll,
            compatibility={key: state.clone() for key, state in self.compatibility.items()},
            review_status=self.review_status,
        )


@dataclass(slots=True)
class MainModlist:
    entries: list[ModlistEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.entries, list):
            raise ModelValidationError("MainModlist.entries must be a list.")

    def validate(self, known_engine_ids: set[str] | None = None) -> None:
        seen: set[tuple[EntryType, str]] = set()
        for index, entry in enumerate(self.entries):
            if not isinstance(entry, ModlistEntry):
                raise ModelValidationError(f"Entry at position {index} is not a ModlistEntry.")
            identity = (entry.entry_type, entry.name)
            if identity in seen:
                raise ModelValidationError(
                    f"Duplicate {entry.entry_type.value} name at position {index}: {entry.name!r}."
                )
            seen.add(identity)
            if entry.entry_type is EntryType.SEPARATOR:
                if entry.active is not None or entry.has_dll is not None or entry.compatibility:
                    raise ModelValidationError(f"Separator at position {index} has mod-only fields.")
                continue
            if known_engine_ids is not None:
                unknown = set(entry.compatibility) - known_engine_ids
                if unknown:
                    raise ModelValidationError(
                        f"Entry {entry.name!r} references unregistered engines: {sorted(unknown)}."
                    )
            for engine_id, state in entry.compatibility.items():
                if not isinstance(engine_id, str) or not engine_id.strip():
                    raise ModelValidationError("Compatibility keys must be non-empty engine IDs.")
                if not isinstance(state, EngineState):
                    raise ModelValidationError(
                        f"Compatibility for {entry.name!r}/{engine_id!r} must be EngineState."
                    )
                _require_bool_or_none(state.compatible, f"{engine_id}.compatible")
                _require_bool_or_none(state.active, f"{engine_id}.active")

    @staticmethod
    def csv_headers(engine_ids: list[str] | tuple[str, ...]) -> list[str]:
        headers = ["Name", "Type", "HasDLL", "Active"]
        for engine_id in engine_ids:
            headers.extend((engine_id, f"{engine_id}_active"))
        return headers

    @staticmethod
    def to_csv_row(entry: ModlistEntry, engine_ids: list[str] | tuple[str, ...]) -> list[str]:
        def encode(value: bool | None) -> str:
            return "" if value is None else ("1" if value else "0")

        if entry.entry_type is EntryType.SEPARATOR:
            return [entry.name, EntryType.SEPARATOR.value, "", "", *( [""] * (2 * len(engine_ids)) )]

        row = [entry.name, EntryType.MOD.value, encode(entry.has_dll), encode(entry.active)]
        for engine_id in engine_ids:
            state = entry.compatibility.get(engine_id, EngineState())
            row.extend((encode(state.compatible), encode(state.active)))
        return row

    def clone(self) -> "MainModlist":
        return MainModlist([entry.clone() for entry in self.entries])


def entry_to_dict(entry: ModlistEntry, *, include_review: bool = True) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": entry.name,
        "entry_type": entry.entry_type.value,
        "active": entry.active,
        "has_dll": entry.has_dll,
        "compatibility": {
            engine_id: {"compatible": state.compatible, "active": state.active}
            for engine_id, state in entry.compatibility.items()
        },
    }
    if include_review:
        result["review_status"] = entry.review_status.value
    return result


def entry_from_dict(data: dict[str, Any]) -> ModlistEntry:
    return ModlistEntry(
        name=data["name"],
        entry_type=EntryType(data.get("entry_type", EntryType.MOD.value)),
        active=data.get("active", False),
        has_dll=data.get("has_dll", data.get("hasdll")),
        compatibility=dict(data.get("compatibility", {})),
        review_status=ReviewStatus(data.get("review_status", ReviewStatus.UNSET.value)),
    )

"""Non-destructive, position-aware merge planning and activation reconciliation."""

from __future__ import annotations

from dataclasses import dataclass, field

from .enums import EntryType, SourceScope
from .errors import ModelValidationError
from .models import EngineState, MainModlist, ModlistEntry


@dataclass(slots=True)
class MergePreview:
    proposed: MainModlist
    new_entries: list[str] = field(default_factory=list)
    missing_candidates: list[str] = field(default_factory=list)
    ignored_missing: list[str] = field(default_factory=list)
    retained_missing: list[str] = field(default_factory=list)
    effective_source_boundary: int | None = None
    boundary_anchor: str | None = None
    warnings: list[str] = field(default_factory=list)


def _key(entry: ModlistEntry) -> tuple[EntryType, str]:
    return entry.entry_type, entry.name


def infer_effective_boundary(source: MainModlist) -> int | None:
    active_positions = [
        index for index, entry in enumerate(source.entries)
        if entry.entry_type is EntryType.MOD and entry.active is True
    ]
    return active_positions[-1] if active_positions else None


def _new_entry_from_source(entry: ModlistEntry, engine_ids: tuple[str, ...]) -> ModlistEntry:
    result = entry.clone()
    if result.entry_type is EntryType.MOD:
        for engine_id in engine_ids:
            result.compatibility.setdefault(engine_id, EngineState(compatible=True))
    return result


def _reconcile_dll_activation(main_entry: ModlistEntry, source_entry: ModlistEntry) -> None:
    """Apply the documented HasDLL=True activation matrix.

    A global disable clears every per-engine active flag. A global enable turns
    on versions known compatible, turns off versions known incompatible, and
    leaves unknown compatibility/activation unresolved. Non-DLL and
    unclassified mods are intentionally not changed by this automation.
    """
    if main_entry.entry_type is not EntryType.MOD or main_entry.has_dll is not True:
        return

    main_entry.active = bool(source_entry.active)
    if source_entry.active is False:
        for engine_id, state in tuple(main_entry.compatibility.items()):
            main_entry.compatibility[engine_id] = EngineState(state.compatible, False)
        return

    for engine_id, state in tuple(main_entry.compatibility.items()):
        if state.compatible is True:
            engine_active = True
        elif state.compatible is False:
            engine_active = False
        else:
            engine_active = None
        main_entry.compatibility[engine_id] = EngineState(state.compatible, engine_active)


def preview_merge(
    main: MainModlist,
    source: MainModlist,
    *,
    scope: SourceScope = SourceScope.ASK,
    remove_missing: set[str] | None = None,
    boundary_override: int | None = None,
    engine_ids: tuple[str, ...] | list[str] | None = None,
    source_engine_id: str | None = None,
) -> MergePreview:
    """Prepare a proposal; neither input is mutated and removals need approval."""
    if not isinstance(main, MainModlist) or not isinstance(source, MainModlist):
        raise ModelValidationError("preview_merge expects two MainModlist objects.")
    source_scope = SourceScope(scope)
    old, incoming = main.clone(), source.clone()
    configured = tuple(engine_ids or sorted({
        engine_id for entry in old.entries for engine_id in entry.compatibility
    }))
    old.validate(set(configured) if configured else None)
    incoming.validate()
    if source_engine_id is not None and configured and source_engine_id not in configured:
        raise ModelValidationError(f"Unknown source engine ID: {source_engine_id!r}.")

    boundary = boundary_override if boundary_override is not None else infer_effective_boundary(incoming)
    if boundary is not None and not 0 <= boundary < len(incoming.entries):
        raise ModelValidationError("boundary_override is outside the source list.")

    result = MergePreview(proposed=old.clone(), effective_source_boundary=boundary)
    old_by_key = {_key(entry): index for index, entry in enumerate(old.entries)}
    source_keys = {_key(entry) for entry in incoming.entries}
    result.new_entries = [entry.name for entry in incoming.entries if _key(entry) not in old_by_key]

    ordered = [entry.clone() for entry in old.entries]
    ordered_by_key = {_key(entry): entry for entry in ordered}
    for source_entry in incoming.entries:
        existing = ordered_by_key.get(_key(source_entry))
        if existing is not None:
            _reconcile_dll_activation(existing, source_entry)

    anchors = [
        (source_index, old_by_key[_key(entry)], entry)
        for source_index, entry in enumerate(incoming.entries)
        if _key(entry) in old_by_key
    ]
    prefix_anchors = [item for item in anchors if boundary is not None and item[0] <= boundary]
    main_boundary: int | None = None
    if prefix_anchors:
        last = prefix_anchors[-1]
        result.boundary_anchor = last[2].name
        main_boundary = last[1]

    missing = [(index, entry) for index, entry in enumerate(old.entries) if _key(entry) not in source_keys]
    if source_scope is SourceScope.ASK:
        result.warnings.append("Source scope requires a user decision: complete or partial.")
        candidates: set[tuple[EntryType, str]] = set()
    elif source_scope is SourceScope.PARTIAL:
        candidates = set()
    elif boundary is None:
        candidates = set()
        result.warnings.append("No active source mod establishes a boundary; no removal candidates were inferred.")
    elif main_boundary is not None:
        candidates = {_key(entry) for index, entry in missing if index <= main_boundary}
    else:
        candidates = {_key(entry) for _, entry in missing}
        if missing:
            result.warnings.append("No common anchor exists; absent entries are candidates only because the source was declared complete.")

    for _, entry in missing:
        (result.missing_candidates if _key(entry) in candidates else result.ignored_missing).append(entry.name)

    approval = remove_missing or set()
    name_counts: dict[str, int] = {}
    for _, entry in missing:
        if _key(entry) in candidates:
            name_counts[entry.name] = name_counts.get(entry.name, 0) + 1
    removed = {
        key for key in candidates
        if key[1] in approval and name_counts.get(key[1]) == 1
    }
    result.retained_missing = [
        entry.name for _, entry in missing if _key(entry) in candidates and _key(entry) not in removed
    ]
    ordered = [entry for entry in ordered if _key(entry) not in removed]
    ordered_keys = {_key(entry) for entry in ordered}

    # Insert contiguous source-only runs around the nearest surviving anchors.
    index = 0
    while index < len(incoming.entries):
        if _key(incoming.entries[index]) in old_by_key:
            index += 1
            continue
        run_start = index
        run: list[ModlistEntry] = []
        while index < len(incoming.entries) and _key(incoming.entries[index]) not in old_by_key:
            run.append(_new_entry_from_source(incoming.entries[index], configured))
            index += 1
        next_key = next(
            (_key(item) for item in incoming.entries[index:] if _key(item) in ordered_keys),
            None,
        )
        if next_key is not None:
            insertion = next(i for i, item in enumerate(ordered) if _key(item) == next_key)
        else:
            previous_key = next(
                (_key(item) for item in reversed(incoming.entries[:run_start]) if _key(item) in ordered_keys),
                None,
            )
            insertion = (
                next(i for i, item in enumerate(ordered) if _key(item) == previous_key) + 1
                if previous_key is not None else len(ordered)
            )
        ordered[insertion:insertion] = run
        ordered_keys.update(_key(item) for item in run)

    result.proposed = MainModlist(ordered)
    result.proposed.validate(set(configured) if configured else None)
    return result

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .enums import EntryType
from .models import MasterModlist, ModlistEntry, entry_to_dict, entry_from_dict


class SourceScope(str, Enum):
    ASK = "ask"
    COMPLETE = "complete"
    PARTIAL = "partial"


@dataclass(slots=True)
class MergePreview:
    proposed: MasterModlist
    new_entries: list[str] = field(default_factory=list)
    missing_candidates: list[str] = field(default_factory=list)
    ignored_missing: list[str] = field(default_factory=list)
    retained_missing: list[str] = field(default_factory=list)
    effective_source_boundary: int | None = None
    boundary_anchor: str | None = None
    warnings: list[str] = field(default_factory=list)


def _key(entry: ModlistEntry) -> tuple[str, str]:
    return (entry.entry_type.value, entry.name)


def infer_effective_boundary(source: MasterModlist) -> int | None:
    """Index of last active mod; trailing disabled entries do not extend boundary."""
    active_positions = [
        i for i, entry in enumerate(source.entries)
        if entry.entry_type is EntryType.MOD and entry.active is True
    ]
    return active_positions[-1] if active_positions else None


def preview_merge(
    master: MasterModlist,
    source: MasterModlist,
    *,
    scope: SourceScope = SourceScope.ASK,
    remove_missing: set[str] | None = None,
    boundary_override: int | None = None,
) -> MergePreview:
    """Build a non-destructive merge proposal.

    `remove_missing` contains entry names explicitly approved for removal.
    The proposal never mutates either input list.
    """
    old = master.clone()
    incoming = source.clone()
    source_scope = SourceScope(scope)
    boundary = boundary_override if boundary_override is not None else infer_effective_boundary(incoming)
    result = MergePreview(proposed=old.clone(), effective_source_boundary=boundary)

    old_by_key = {_key(e): i for i, e in enumerate(old.entries)}
    source_keys = {_key(e) for e in incoming.entries}
    new_source_entries = [e for e in incoming.entries if _key(e) not in old_by_key]
    result.new_entries = [e.name for e in new_source_entries]

    # Existing entries appearing in source are positional anchors.
    anchors = [
        (source_index, old_by_key[_key(entry)], entry)
        for source_index, entry in enumerate(incoming.entries)
        if _key(entry) in old_by_key
    ]
    if anchors:
        boundary_anchors = [a for a in anchors if boundary is not None and a[0] <= boundary]
        if boundary_anchors:
            last_anchor = boundary_anchors[-1]
            result.boundary_anchor = last_anchor[2].name
            master_boundary = last_anchor[1]
        else:
            master_boundary = None
    else:
        master_boundary = None
        if boundary is not None:
            result.warnings.append(
                "No existing entries anchor the imported list; missing-entry detection is conservative."
            )

    missing = [
        (i, e) for i, e in enumerate(old.entries)
        if _key(e) not in source_keys
    ]

    if source_scope is SourceScope.ASK:
        result.warnings.append("Source scope requires user confirmation (complete or partial).")
        candidate_keys: set[tuple[str, str]] = set()
    elif source_scope is SourceScope.PARTIAL:
        candidate_keys = set()
    elif master_boundary is not None:
        candidate_keys = {_key(e) for i, e in missing if i <= master_boundary}
    else:
        # With no common anchor, a declared complete source means all missing entries
        # are candidates, but the UI must show the warning and ask for confirmation.
        candidate_keys = {_key(e) for _, e in missing}
        if missing:
            result.warnings.append(
                "No common anchor: all absent entries are candidates only because source was declared complete."
            )

    for master_index, entry in missing:
        key = _key(entry)
        if key in candidate_keys:
            result.missing_candidates.append(entry.name)
        else:
            result.ignored_missing.append(entry.name)

    approved = remove_missing or set()
    removed_keys = {
        key for key in candidate_keys
        if next((e.name for _, e in missing if _key(e) == key), None) in approved
    }
    result.retained_missing = [
        e.name for _, e in missing
        if _key(e) in candidate_keys and _key(e) not in removed_keys
    ]

    # Preserve the master order, deleting only explicitly approved candidates.
    ordered = [entry_from_dict(entry_to_dict(e)) for e in old.entries if _key(e) not in removed_keys]

    # Insert source-only entries relative to the preceding source entry. This keeps
    # existing master entries' relative order stable and preserves imported order.
    for source_index, incoming_entry in enumerate(incoming.entries):
        key = _key(incoming_entry)
        if key in old_by_key:
            continue
        new_entry = entry_from_dict(entry_to_dict(incoming_entry))
        preceding_key = None
        for prior in reversed(incoming.entries[:source_index]):
            if _key(prior) in {_key(e) for e in ordered}:
                preceding_key = _key(prior)
                break
        if preceding_key is not None:
            insertion = next(i for i, e in enumerate(ordered) if _key(e) == preceding_key) + 1
            # Keep adjacent source-only entries in their original order.
            while insertion < len(ordered) and getattr(ordered[insertion], "_merge_source_index", None) == source_index - 1:
                insertion += 1
            ordered.insert(insertion, new_entry)
        else:
            following_key = next(
                (_key(e) for e in incoming.entries[source_index + 1:] if _key(e) in {_key(x) for x in ordered}),
                None,
            )
            if following_key is not None:
                insertion = next(i for i, e in enumerate(ordered) if _key(e) == following_key)
                ordered.insert(insertion, new_entry)
            else:
                ordered.append(new_entry)

    result.proposed = MasterModlist(ordered)
    result.proposed.validate()
    return result

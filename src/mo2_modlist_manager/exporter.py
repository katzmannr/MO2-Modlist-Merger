from __future__ import annotations

from .enums import EntryType
from .errors import ModelValidationError
from .models import MasterModlist


def export_modlist_text(master: MasterModlist, *, include_header: bool = True) -> str:
    master.validate()
    lines = ["# This file was automatically created by MO2 Modlist Manager."] if include_header else []
    for entry in master.entries:
        if entry.entry_type is EntryType.SEPARATOR:
            lines.append(f"+{entry.name}")
        else:
            lines.append(("+" if entry.active else "-") + entry.name)
    return "\n".join(lines) + ("\n" if lines else "")

def export_for_engine(master: MasterModlist, engine_id: str, *, include_header: bool = True) -> str:
    """Export enabled mods for an engine, retaining separators and activation state.

    Incompatible and unknown entries are not silently removed or disabled here:
    export is a representation operation, not an activation manager. The caller
    must explicitly choose a policy in a later UI/service layer.
    """
    for entry in master.entries:
        if entry.entry_type is EntryType.MOD and engine_id not in entry.compatibility:
            raise ModelValidationError(
                f"Entry {entry.name!r} has no compatibility value for engine {engine_id!r}."
            )
    return export_modlist_text(master, include_header=include_header)

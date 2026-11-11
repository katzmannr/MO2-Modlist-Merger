from __future__ import annotations

from .enums import EntryType
from .errors import ModelValidationError
from .models import MainModlist


def export_modlist_text(main_list: MainModlist, *, include_header: bool = True) -> str:
    main_list.validate()
    lines = ["# This file was automatically created by MO2 Modlist Manager."] if include_header else []
    for entry in main_list.entries:
        if entry.entry_type is EntryType.SEPARATOR:
            lines.append(f"+{entry.name}")
        else:
            lines.append(("+" if entry.active else "-") + entry.name)
    return "\n".join(lines) + ("\n" if lines else "")


def export_for_engine(main_list: MainModlist, engine_id: str, *, include_header: bool = True) -> str:
    """Serialize current activation; compatibility filtering remains a separate policy."""
    for entry in main_list.entries:
        if entry.entry_type is EntryType.MOD and engine_id not in entry.compatibility:
            raise ModelValidationError(
                f"Entry {entry.name!r} has no compatibility value for engine {engine_id!r}."
            )
    return export_modlist_text(main_list, include_header=include_header)

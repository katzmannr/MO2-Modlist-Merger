from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .enums import EntryType
from .errors import ModlistManagerError
from .models import MasterModlist, ModlistEntry


class ModlistParseError(ModlistManagerError):
    pass


@dataclass(frozen=True, slots=True)
class ParsedModlist:
    master: MasterModlist
    source_path: str | None = None
    source_mtime: float | None = None
    raw_sha256: str | None = None


def _is_separator(name: str) -> bool:
    # MO2 represents separators in modlist.txt with the reserved separator_ prefix.
    return name.lower().startswith("_separator")


def parse_modlist_text(text: str, *, strict: bool = True) -> MasterModlist:
    entries: list[ModlistEntry] = []
    seen: set[tuple[EntryType, str]] = set()

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if len(line) < 2 or line[0] not in "+-":
            if strict:
                raise ModlistParseError(
                    f"Malformed modlist line {line_number}: expected '+' or '-' prefix."
                )
            continue

        name = line[1:]
        if not name:
            if strict:
                raise ModlistParseError(f"Empty entry on modlist line {line_number}.")
            continue

        entry_type = EntryType.SEPARATOR if _is_separator(name) else EntryType.MOD
        identity = (entry_type, name)
        if identity in seen:
            raise ModlistParseError(
                f"Duplicate {entry_type.value} entry on line {line_number}: {name!r}"
            )
        seen.add(identity)

        if entry_type is EntryType.SEPARATOR:
            entries.append(ModlistEntry(name=name, entry_type=EntryType.SEPARATOR))
        else:
            entries.append(ModlistEntry(
                name=name, entry_type=EntryType.MOD, active=(line[0] == "+")
            ))

    return MasterModlist(entries)


def parse_modlist_file(path: str | Path, *, strict: bool = True) -> ParsedModlist:
    import hashlib
    source = Path(path)
    try:
        raw = source.read_bytes()
        text = raw.decode("utf-8-sig")
        stat = source.stat()
    except (OSError, UnicodeDecodeError) as exc:
        raise ModlistParseError(f"Cannot read modlist {source}: {exc}") from exc
    return ParsedModlist(
        master=parse_modlist_text(text, strict=strict),
        source_path=str(source.resolve()),
        source_mtime=stat.st_mtime,
        raw_sha256=hashlib.sha256(raw).hexdigest(),
    )

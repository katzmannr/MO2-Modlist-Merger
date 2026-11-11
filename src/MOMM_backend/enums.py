"""Shared MOMM enumerations."""

from enum import Enum


class EntryType(str, Enum):
    MOD = "mod"
    SEPARATOR = "separator"


class EngineStatus(str, Enum):
    """Availability of an engine mod. Active in mod list (if compatible)"""
    ACTIVE = "active"
    COMPATIBLE = "compatible"


class ModType(str, Enum):
    NON_SKSE = "non_skse"
    SKSE = "skse"


class ReviewStatus(str, Enum):
    UNSET = "unset"
    UNFINISHED = "unfinished"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class SourceScope(str, Enum):
    ASK = "ask"
    COMPLETE = "complete"
    PARTIAL = "partial"

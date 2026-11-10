from enum import Enum


class EntryType(str, Enum):
    MOD = "mod"
    SEPARATOR = "separator"


class EngineStatus(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"


class ModType(str, Enum):
    NON_SKSE = "non_skse"
    SKSE = "skse"


class ReviewStatus(str, Enum):
    UNSET = "unset"
    DONE = "done"

"""Application exceptions and structured diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .models import MainModlist

IssueSeverity = Literal["fatal", "error", "warning"]

class ModlistManagerError(Exception):
    """Base class for expected, user-presentable application errors."""

class ConfigurationError(ModlistManagerError):
    """Settings are missing, malformed, or semantically invalid."""

class ModelValidationError(ModlistManagerError):
    """An in-memory model violates application invariants."""

class CSVStoreError(ModlistManagerError):
    """A CSV cannot be written or a persistence operation cannot proceed."""


@dataclass(frozen=True, slots=True)
class CSVIssue:
    """One structured diagnostic from a CSV import."""

    row: int | None
    column: str | None
    message: str
    severity: IssueSeverity = "error"


@dataclass(slots=True)
class CSVLoadResult:
    """Atomic result of a CSV load. Fatal / Error result in empty main_list. Only Full a list is valid"""

    main_list: MainModlist | None
    issues: list[CSVIssue] = field(default_factory=list)
    stopped_early: bool = False

    @property
    def success(self) -> bool:
        return self.main_list is not None and not any(
            issue.severity in {"fatal", "error"} for issue in self.issues
        )

    @property
    def errors(self) -> tuple[CSVIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity in {"fatal", "error"})

    @property
    def warnings(self) -> tuple[CSVIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")


@dataclass(frozen=True, slots=True)
class WorkflowIssue:
    """One user-presentable diagnostic produced while committing a workflow."""

    operation: str
    message: str
    severity: IssueSeverity = "error"
    path: str | None = None


@dataclass(slots=True)
class WorkflowCommitResult:
    """Result of a main-list commit; failures are returned."""

    patch: dict | None = None
    issues: list[WorkflowIssue] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.patch is not None and not any(
            issue.severity in {"fatal", "error"} for issue in self.issues
        )

    @property
    def errors(self) -> tuple[WorkflowIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity in {"fatal", "error"})

    @property
    def warnings(self) -> tuple[WorkflowIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")

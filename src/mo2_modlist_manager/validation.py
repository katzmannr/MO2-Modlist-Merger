from __future__ import annotations

from .config import AppSettings
from .errors import ModelValidationError
from .models import MasterModlist


def validate_settings(settings: AppSettings) -> list[str]:
    """Return human-readable warnings; structural errors are raised during loading."""
    warnings: list[str] = []
    if not settings.engines.active():
        warnings.append("No active game engines are configured.")
    for index, instance in enumerate(settings.instances):
        if not isinstance(instance, dict):
            raise ModelValidationError(f"Instance at index {index} must be an object.")
        if not instance.get("name"):
            warnings.append(f"Instance at index {index} has no name.")
        if not instance.get("path"):
            warnings.append(f"Instance at index {index} has no path.")
    keep = settings.backup.get("keep_snapshots", 10)
    if not isinstance(keep, int) or isinstance(keep, bool) or keep < 1:
        raise ModelValidationError("backup.keep_snapshots must be a positive integer.")
    scope = settings.merge.get("default_source_scope", "ask")
    if scope not in {"ask", "complete", "partial"}:
        raise ModelValidationError(
            "merge.default_source_scope must be 'ask', 'complete', or 'partial'."
        )
    return warnings


def validate_master(master: MasterModlist, settings: AppSettings) -> None:
    master.validate(set(settings.engines.ids()))

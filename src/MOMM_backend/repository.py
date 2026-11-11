from __future__ import annotations

import shutil
from pathlib import Path

from .csv_store import MainCSVStore
from .errors import CSVLoadResult, CSVStoreError
from .history import HistoryManager, build_patch, main_revision
from .models import MainModlist
from .workflow import ReviewWorkflowStore


class MainRepository:
    """Coordinates persistence; application state remains owned by its caller."""

    def __init__(
        self,
        main_path: str | Path,
        engine_ids: tuple[str, ...] | list[str],
        engine_active: tuple[str, ...] | list[str],
        *,
        workflow_path: str | Path | None = None,
        history: HistoryManager | None = None,
    ) -> None:
        self.main_path = Path(main_path)
        self.workflow_path = Path(workflow_path) if workflow_path else self.main_path.with_name("workflow.json")
        self.engine_ids = tuple(engine_ids)
        self.engine_active = tuple(engine_active)
        self.csv_store = MainCSVStore(self.engine_ids)
        self.workflow_store = ReviewWorkflowStore()
        self.history = history

    def load(self) -> CSVLoadResult:
        result = self.csv_store.load(self.main_path)
        if result.success and result.main_list is not None:
            self.workflow_store.load(self.workflow_path, result.main_list)
        return result

    def commit(self, before: MainModlist, after: MainModlist, *, reason: str) -> dict:
        after.validate(set(self.engine_ids))
        loaded = self.csv_store.load(self.main_path)
        if not loaded.success or loaded.main_list is None:
            details = "; ".join(issue.message for issue in loaded.issues)
            raise CSVStoreError(f"Cannot commit because the current main CSV is invalid: {details}")
        if main_revision(before, self.engine_ids) != main_revision(loaded.main_list, self.engine_ids):
            raise RuntimeError("Main changed since this operation was prepared; reload before committing.")

        patch = build_patch(before, after, self.engine_ids, reason=reason)
        self.main_path.parent.mkdir(parents=True, exist_ok=True)
        backup_csv = self.main_path.with_suffix(self.main_path.suffix + ".bak")
        backup_workflow = self.workflow_path.with_suffix(self.workflow_path.suffix + ".bak")
        had_workflow = self.workflow_path.exists()
        shutil.copy2(self.main_path, backup_csv)
        if had_workflow:
            shutil.copy2(self.workflow_path, backup_workflow)

        try:
            self.csv_store.save(after, self.main_path)
            self.workflow_store.save(self.workflow_path, after)
            if self.history:
                self.history.write_patch(patch)
                self.history.snapshot(self.main_path)
        except Exception:
            shutil.copy2(backup_csv, self.main_path)
            if had_workflow:
                shutil.copy2(backup_workflow, self.workflow_path)
            else:
                self.workflow_path.unlink(missing_ok=True)
            raise
        return patch

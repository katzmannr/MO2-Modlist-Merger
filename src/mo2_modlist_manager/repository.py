from __future__ import annotations

import shutil
from pathlib import Path

from .csv_store import MasterCSVStore
from .history import HistoryManager, build_patch, master_revision
from .models import MasterModlist
from .workflow import ReviewWorkflowStore


class MasterRepository:
    """Coordinates master CSV, workflow sidecar, backups and patch commits."""

    def __init__(
        self,
        master_path: str | Path,
        engine_ids: tuple[str, ...] | list[str],
        engine_active: tuple[str, ...] | list[str],
        *,
        workflow_path: str | Path | None = None,
        history: HistoryManager | None = None,
    ):
        self.master_path = Path(master_path)
        self.workflow_path = Path(workflow_path) if workflow_path else self.master_path.with_name("workflow.json")
        self.engine_ids = tuple(engine_ids)
        self.engine_active = tuple(engine_ids)
        self.csv_store = MasterCSVStore(self.engine_ids)
        self.workflow_store = ReviewWorkflowStore()
        self.history = history

    def load(self) -> MasterModlist:
        master = self.csv_store.load(self.master_path)
        self.workflow_store.load(self.workflow_path, master)
        return master

    def commit(self, before: MasterModlist, after: MasterModlist, *, reason: str) -> dict:
        after.validate(set(self.engine_ids))
        current = self.csv_store.load(self.master_path)
        expected = master_revision(before, self.engine_ids)
        actual = master_revision(current, self.engine_ids)
        if expected != actual:
            raise RuntimeError("Master changed since this operation was prepared; reload before committing.")

        patch = build_patch(before, after, self.engine_ids, reason=reason)
        self.master_path.parent.mkdir(parents=True, exist_ok=True)
        backup_csv = self.master_path.with_suffix(self.master_path.suffix + ".bak")
        backup_workflow = self.workflow_path.with_suffix(self.workflow_path.suffix + ".bak")
        had_workflow = self.workflow_path.exists()

        shutil.copy2(self.master_path, backup_csv)
        if had_workflow:
            shutil.copy2(self.workflow_path, backup_workflow)

        try:
            self.csv_store.save(after, self.master_path)
            self.workflow_store.save(self.workflow_path, after)
            if self.history:
                self.history.write_patch(patch)
                self.history.snapshot(self.master_path)
        except Exception:
            shutil.copy2(backup_csv, self.master_path)
            if had_workflow:
                shutil.copy2(backup_workflow, self.workflow_path)
            else:
                self.workflow_path.unlink(missing_ok=True)
            raise
        return patch

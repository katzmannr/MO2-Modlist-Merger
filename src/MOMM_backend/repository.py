from __future__ import annotations

import shutil
from pathlib import Path

from .csv_store import MainCSVStore
from .errors import CSVLoadResult, WorkflowCommitResult, WorkflowIssue
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

    def commit(self, before: MainModlist, after: MainModlist, *, reason: str) -> WorkflowCommitResult:
        """Persist a proposed main-list change and return UI-safe diagnostics.

        Expected persistence, validation, and concurrency failures are reported
        through the result instead of escaping as exceptions. The in-memory
        lists are never modified by this method.
        """
        try:
            after.validate(set(self.engine_ids))
        except Exception as exc:
            return WorkflowCommitResult(issues=[
                WorkflowIssue(
                    operation="validate_proposed_main_list",
                    message=str(exc),
                    path=str(self.main_path),
                )
            ])

        try:
            loaded = self.csv_store.load(self.main_path)
        except Exception as exc:
            return WorkflowCommitResult(issues=[
                WorkflowIssue(
                    operation="load_current_main_list",
                    message=f"Could not read the current main CSV: {exc}",
                    path=str(self.main_path),
                )
            ])

        if not loaded.success or loaded.main_list is None:
            issues = [
                WorkflowIssue(
                    operation="load_current_main_list",
                    message=issue.message,
                    severity=issue.severity,
                    path=str(self.main_path),
                )
                for issue in loaded.issues
            ]
            if not issues:
                issues.append(WorkflowIssue(
                    operation="load_current_main_list",
                    message="The current main CSV could not be loaded.",
                    path=str(self.main_path),
                ))
            return WorkflowCommitResult(issues=issues)

        try:
            if main_revision(before, self.engine_ids) != main_revision(loaded.main_list, self.engine_ids):
                return WorkflowCommitResult(issues=[
                    WorkflowIssue(
                        operation="check_main_revision",
                        message="The main list changed since this operation was prepared. Reload before committing.",
                        path=str(self.main_path),
                    )
                ])
            patch = build_patch(before, after, self.engine_ids, reason=reason)
        except Exception as exc:
            return WorkflowCommitResult(issues=[
                WorkflowIssue(
                    operation="prepare_commit",
                    message=f"Could not prepare the main-list change: {exc}",
                    path=str(self.main_path),
                )
            ])

        backup_csv = self.main_path.with_suffix(self.main_path.suffix + ".bak")
        backup_workflow = self.workflow_path.with_suffix(self.workflow_path.suffix + ".bak")
        had_workflow = self.workflow_path.exists()
        main_backup_ready = False
        workflow_backup_ready = False
        main_write_started = False
        workflow_write_started = False
        patch_path: Path | None = None
        snapshot_path: Path | None = None
        stage = "create_backups"

        try:
            self.main_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.main_path, backup_csv)
            main_backup_ready = True

            if had_workflow:
                shutil.copy2(self.workflow_path, backup_workflow)
                workflow_backup_ready = True

            stage = "write_main_csv"
            main_write_started = True
            self.csv_store.save(after, self.main_path)

            stage = "write_workflow_metadata"
            workflow_write_started = True
            self.workflow_store.save(self.workflow_path, after)

            if self.history:
                stage = "write_history"
                patch_path = self.history.write_patch(patch)
                snapshot_path = self.history.snapshot(self.main_path)
        except Exception as exc:
            issues = [
                WorkflowIssue(
                    operation=stage,
                    message=f"Commit failed during {stage.replace('_', ' ')}: {exc}",
                    path=str(self.main_path if stage != "write_workflow_metadata" else self.workflow_path),
                )
            ]

            if main_write_started:
                if main_backup_ready:
                    try:
                        shutil.copy2(backup_csv, self.main_path)
                    except Exception as rollback_exc:
                        issues.append(WorkflowIssue(
                            operation="rollback_main_csv",
                            message=f"Could not restore the previous main CSV: {rollback_exc}",
                            path=str(self.main_path),
                        ))
                else:
                    issues.append(WorkflowIssue(
                        operation="rollback_main_csv",
                        message="The previous main CSV backup was not available; automatic restoration was not possible.",
                        path=str(self.main_path),
                    ))

            if workflow_write_started:
                try:
                    if had_workflow:
                        if not workflow_backup_ready:
                            raise OSError("The previous workflow metadata backup was not available.")
                        shutil.copy2(backup_workflow, self.workflow_path)
                    else:
                        self.workflow_path.unlink(missing_ok=True)
                    temporary_workflow = self.workflow_path.with_suffix(
                        self.workflow_path.suffix + ".tmp"
                    )
                    temporary_workflow.unlink(missing_ok=True)
                except Exception as rollback_exc:
                    issues.append(WorkflowIssue(
                        operation="rollback_workflow_metadata",
                        message=f"Could not restore the previous workflow metadata: {rollback_exc}",
                        path=str(self.workflow_path),
                    ))

            for created_path in (snapshot_path, patch_path):
                if created_path is not None:
                    try:
                        created_path.unlink(missing_ok=True)
                    except Exception as cleanup_exc:
                        issues.append(WorkflowIssue(
                            operation="rollback_history",
                            message=f"Could not remove incomplete history artifact {created_path}: {cleanup_exc}",
                            path=str(created_path),
                        ))

            return WorkflowCommitResult(issues=issues)

        return WorkflowCommitResult(patch=patch)

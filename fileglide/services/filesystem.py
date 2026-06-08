"""File and directory lifecycle operations."""

from __future__ import annotations

import shutil
from pathlib import Path

from fileglide.exceptions import (
    AlreadyExistsError,
    ConfirmRequiredError,
    NotFoundError,
    ValidationError,
)
from fileglide.models import PreviewDetail
from fileglide.services.scope import ScopeService


class FilesystemService:
    """Create, delete, and inspect files or directories inside a scope."""

    def __init__(self, scope_service: ScopeService) -> None:
        self._scope = scope_service

    def create_file(
        self,
        root: str | Path | None,
        target: str | Path,
        *,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> dict[str, object]:
        """Create an empty file within the configured scope."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        if resolved_target.exists() and not exist_ok:
            raise AlreadyExistsError(
                code="file_exists",
                message="File already exists.",
                details={"target": str(resolved_target)},
                path=str(resolved_target),
            )
        if parents:
            resolved_target.parent.mkdir(parents=True, exist_ok=True)
        elif not resolved_target.parent.exists():
            raise NotFoundError(
                code="parent_missing",
                message="Parent directory does not exist.",
                details={"parent": str(resolved_target.parent)},
                path=str(resolved_target.parent),
            )
        resolved_target.touch(exist_ok=exist_ok)
        metadata = self._scope.describe_entry(resolved_root, resolved_target)
        return {"created": True, "entry": metadata}

    def delete_file(
        self,
        root: str | Path | None,
        target: str | Path,
        *,
        dry_run: bool = False,
        confirm: bool = False,
        missing_ok: bool = False,
    ) -> dict[str, object]:
        """Delete a file after preview and confirmation checks."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        if not resolved_target.exists():
            if missing_ok:
                return {
                    "deleted": False,
                    "missing": True,
                    "entry": self._scope.describe_entry(resolved_root, resolved_target),
                }
            raise NotFoundError(
                code="file_missing",
                message="File does not exist.",
                details={"target": str(resolved_target)},
                path=str(resolved_target),
            )
        if not resolved_target.is_file():
            raise ValidationError(
                code="not_a_file",
                message="Target is not a file.",
                details={"target": str(resolved_target)},
                path=str(resolved_target),
            )

        preview = PreviewDetail(
            action="delete_file",
            dry_run=dry_run,
            destructive=True,
            requires_confirmation=not dry_run,
            confirmed=confirm,
            affected_targets=[str(resolved_target)],
            details={"size_bytes": resolved_target.stat().st_size},
        )
        if dry_run:
            return {
                "deleted": False,
                "preview": preview,
                "entry": self._scope.describe_entry(resolved_root, resolved_target),
            }
        if not confirm:
            raise ConfirmRequiredError(
                code="confirm_required",
                message="Deleting a file requires --confirm or --dry-run.",
                details={"preview": preview.__dict__},
                path=str(resolved_target),
            )
        resolved_target.unlink()
        return {
            "deleted": True,
            "preview": preview,
            "entry": self._scope.describe_entry(resolved_root, resolved_target),
        }

    def create_path(
        self,
        root: str | Path | None,
        target: str | Path,
        *,
        parents: bool = True,
        exist_ok: bool = True,
    ) -> dict[str, object]:
        """Create a directory within the configured scope."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        if resolved_target.exists() and not exist_ok:
            raise AlreadyExistsError(
                code="path_exists",
                message="Directory already exists.",
                details={"target": str(resolved_target)},
                path=str(resolved_target),
            )
        resolved_target.mkdir(parents=parents, exist_ok=exist_ok)
        return {
            "created": True,
            "entry": self._scope.describe_entry(resolved_root, resolved_target),
        }

    def delete_path(
        self,
        root: str | Path | None,
        target: str | Path,
        *,
        recursive: bool = False,
        dry_run: bool = False,
        confirm: bool = False,
        missing_ok: bool = False,
    ) -> dict[str, object]:
        """Delete a directory with dry-run and confirmation support."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        if not resolved_target.exists():
            if missing_ok:
                return {
                    "deleted": False,
                    "missing": True,
                    "entry": self._scope.describe_entry(resolved_root, resolved_target),
                }
            raise NotFoundError(
                code="path_missing",
                message="Directory does not exist.",
                details={"target": str(resolved_target)},
                path=str(resolved_target),
            )
        if not resolved_target.is_dir():
            raise ValidationError(
                code="not_a_directory",
                message="Target is not a directory.",
                details={"target": str(resolved_target)},
                path=str(resolved_target),
            )

        descendants = [entry for entry in resolved_target.rglob("*")]
        if descendants and not recursive:
            raise ValidationError(
                code="directory_not_empty",
                message="Directory is not empty. Pass --recursive to delete it.",
                details={
                    "target": str(resolved_target),
                    "descendant_count": len(descendants),
                },
                path=str(resolved_target),
            )

        preview = PreviewDetail(
            action="delete_path",
            dry_run=dry_run,
            destructive=True,
            requires_confirmation=not dry_run,
            confirmed=confirm,
            affected_targets=[str(resolved_target)],
            details={"descendant_count": len(descendants), "recursive": recursive},
        )
        if dry_run:
            return {
                "deleted": False,
                "preview": preview,
                "entry": self._scope.describe_entry(resolved_root, resolved_target),
            }
        if not confirm:
            raise ConfirmRequiredError(
                code="confirm_required",
                message="Deleting a directory requires --confirm or --dry-run.",
                details={"preview": preview.__dict__},
                path=str(resolved_target),
            )

        if recursive:
            shutil.rmtree(resolved_target)
        else:
            resolved_target.rmdir()
        return {
            "deleted": True,
            "preview": preview,
            "entry": self._scope.describe_entry(resolved_root, resolved_target),
        }

    def exists(self, root: str | Path | None, target: str | Path) -> dict[str, object]:
        """Return existence metadata for a scoped target."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        return {"entry": self._scope.describe_entry(resolved_root, resolved_target)}

"""Filesystem lifecycle operations for files and directories."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from fileglide.exceptions import (
    AlreadyExistsError,
    ConfirmRequiredError,
    NotFoundError,
    ValidationError,
)
from fileglide.models import PreviewDetail
from fileglide.services.scope import ScopeService


class FilesystemService:
    """Provide scoped lifecycle operations for files and directories."""

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

    def move_file(
        self,
        root: str | Path | None,
        source: str | Path,
        destination: str | Path,
        *,
        destination_root: str | Path | None = None,
        dry_run: bool = False,
        confirm: bool = False,
    ) -> dict[str, object]:
        """Move a file while allowing separate source and destination roots."""

        move_context = self._prepare_move(
            root,
            source,
            destination,
            destination_root=destination_root,
            expected_kind="file",
        )
        preview = self._build_move_preview(
            action="file.move",
            move_context=move_context,
            dry_run=dry_run,
            confirm=confirm,
        )
        if dry_run:
            return self._build_move_response(
                move_context=move_context,
                preview=preview,
                moved=False,
            )
        if not confirm:
            raise ConfirmRequiredError(
                code="confirm_required",
                message="Moving a file requires --confirm or --dry-run.",
                details={"preview": preview.__dict__},
                path=str(move_context["source"]),
            )

        shutil.move(str(move_context["source"]), str(move_context["destination"]))
        return self._build_move_response(
            move_context=move_context,
            preview=preview,
            moved=True,
        )

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

    def move_path(
        self,
        root: str | Path | None,
        source: str | Path,
        destination: str | Path,
        *,
        destination_root: str | Path | None = None,
        dry_run: bool = False,
        confirm: bool = False,
    ) -> dict[str, object]:
        """Move a directory together with all nested descendants."""

        move_context = self._prepare_move(
            root,
            source,
            destination,
            destination_root=destination_root,
            expected_kind="directory",
        )
        preview = self._build_move_preview(
            action="path.move",
            move_context=move_context,
            dry_run=dry_run,
            confirm=confirm,
        )
        if dry_run:
            return self._build_move_response(
                move_context=move_context,
                preview=preview,
                moved=False,
            )
        if not confirm:
            raise ConfirmRequiredError(
                code="confirm_required",
                message="Moving a directory requires --confirm or --dry-run.",
                details={"preview": preview.__dict__},
                path=str(move_context["source"]),
            )

        shutil.move(str(move_context["source"]), str(move_context["destination"]))
        return self._build_move_response(
            move_context=move_context,
            preview=preview,
            moved=True,
        )

    def exists(self, root: str | Path | None, target: str | Path) -> dict[str, object]:
        """Return existence metadata for a scoped target."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        return {"entry": self._scope.describe_entry(resolved_root, resolved_target)}

    def _prepare_move(
        self,
        root: str | Path | None,
        source: str | Path,
        destination: str | Path,
        *,
        destination_root: str | Path | None,
        expected_kind: str,
    ) -> dict[str, Any]:
        """Resolve and validate move sources, destinations, and edge cases."""

        (
            source_root,
            resolved_source,
            resolved_destination_root,
            resolved_destination,
        ) = self._scope.resolve_move_pair(
            root,
            source,
            destination_root,
            destination,
        )
        if resolved_source == resolved_destination:
            raise ValidationError(
                code="same_move_target",
                message="Source and destination resolve to the same path.",
                details={
                    "source": str(resolved_source),
                    "destination": str(resolved_destination),
                },
                path=str(resolved_source),
            )
        if not resolved_source.exists():
            raise NotFoundError(
                code="move_source_missing",
                message="Move source does not exist.",
                details={"source": str(resolved_source)},
                path=str(resolved_source),
            )
        if expected_kind == "file" and not resolved_source.is_file():
            raise ValidationError(
                code="not_a_file",
                message="Source is not a file.",
                details={"source": str(resolved_source)},
                path=str(resolved_source),
            )
        if expected_kind == "directory" and not resolved_source.is_dir():
            raise ValidationError(
                code="not_a_directory",
                message="Source is not a directory.",
                details={"source": str(resolved_source)},
                path=str(resolved_source),
            )
        if resolved_destination.exists():
            raise AlreadyExistsError(
                code="destination_exists",
                message="Destination already exists.",
                details={"destination": str(resolved_destination)},
                path=str(resolved_destination),
            )
        if not resolved_destination.parent.exists():
            raise NotFoundError(
                code="destination_parent_missing",
                message="Destination parent directory does not exist.",
                details={"parent": str(resolved_destination.parent)},
                path=str(resolved_destination.parent),
            )

        descendant_count = 0
        if expected_kind == "directory":
            try:
                resolved_destination.relative_to(resolved_source)
            except ValueError:
                pass
            else:
                raise ValidationError(
                    code="destination_inside_source",
                    message="Destination cannot be inside the source directory.",
                    details={
                        "source": str(resolved_source),
                        "destination": str(resolved_destination),
                    },
                    path=str(resolved_destination),
                )
            descendant_count = sum(1 for _ in resolved_source.rglob("*"))

        return {
            "source_root": source_root,
            "destination_root": resolved_destination_root,
            "source": resolved_source,
            "destination": resolved_destination,
            "expected_kind": expected_kind,
            "cross_root": source_root != resolved_destination_root,
            "descendant_count": descendant_count,
        }

    @staticmethod
    def _build_move_preview(
        *,
        action: str,
        move_context: dict[str, Any],
        dry_run: bool,
        confirm: bool,
    ) -> PreviewDetail:
        """Build a structured preview payload for a move operation."""

        details: dict[str, Any] = {
            "entry_kind": move_context["expected_kind"],
            "cross_root": move_context["cross_root"],
            "source_root": str(move_context["source_root"]),
            "destination_root": str(move_context["destination_root"]),
        }
        if move_context["expected_kind"] == "file":
            details["size_bytes"] = Path(move_context["source"]).stat().st_size
        else:
            details["descendant_count"] = move_context["descendant_count"]
        return PreviewDetail(
            action=action,
            dry_run=dry_run,
            destructive=True,
            requires_confirmation=not dry_run,
            confirmed=confirm,
            affected_targets=[
                str(move_context["source"]),
                str(move_context["destination"]),
            ],
            details=details,
        )

    def _build_move_response(
        self,
        *,
        move_context: dict[str, Any],
        preview: PreviewDetail,
        moved: bool,
    ) -> dict[str, object]:
        """Build the standard response payload for a move operation."""

        return {
            "moved": moved,
            "preview": preview,
            "cross_root": move_context["cross_root"],
            "roots": {
                "source": str(move_context["source_root"]),
                "destination": str(move_context["destination_root"]),
            },
            "source": self._scope.describe_entry(
                Path(move_context["source_root"]),
                Path(move_context["source"]),
            ),
            "destination": self._scope.describe_entry(
                Path(move_context["destination_root"]),
                Path(move_context["destination"]),
            ),
        }

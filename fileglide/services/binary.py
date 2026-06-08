"""Binary-safe file workflows."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from fileglide.exceptions import NotFoundError, ValidationError
from fileglide.services.scope import ScopeService


class BinaryService:
    """Read, write, slice, and copy binary file content."""

    def __init__(self, scope_service: ScopeService) -> None:
        self._scope = scope_service

    def read_bytes(
        self,
        root: str | Path | None,
        target: str | Path,
        *,
        offset: int = 0,
        length: int | None = None,
    ) -> dict[str, Any]:
        """Read all bytes or a selected byte range from a file."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        if not resolved_target.exists():
            raise NotFoundError(
                code="binary_missing",
                message="Binary target does not exist.",
                details={"target": str(resolved_target)},
                path=str(resolved_target),
            )
        payload = resolved_target.read_bytes()
        if offset < 0:
            raise ValidationError(
                code="invalid_offset",
                message="Byte offset must be zero or positive.",
                details={"offset": offset},
                path=str(resolved_target),
            )
        end = len(payload) if length is None else offset + length
        selected = payload[offset:end]
        return {
            "entry": self._scope.describe_entry(resolved_root, resolved_target),
            "offset": offset,
            "length": len(selected),
            "size_bytes": len(payload),
            "content_hex": selected.hex(),
        }

    def write_bytes(
        self,
        root: str | Path | None,
        target: str | Path,
        *,
        data: bytes,
        mode: str = "overwrite",
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Overwrite, append, or insert binary bytes."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        existing = resolved_target.read_bytes() if resolved_target.exists() else b""
        if mode == "overwrite":
            payload = data
        elif mode == "append":
            payload = existing + data
        elif mode == "insert":
            insert_at = len(existing) if offset is None else offset
            if insert_at < 0 or insert_at > len(existing):
                raise ValidationError(
                    code="invalid_insert_offset",
                    message="Insert offset is out of bounds.",
                    details={"offset": offset, "length": len(existing)},
                    path=str(resolved_target),
                )
            payload = existing[:insert_at] + data + existing[insert_at:]
        else:
            raise ValidationError(
                code="invalid_binary_mode",
                message="Binary mode must be overwrite, append, or insert.",
                details={"mode": mode},
                path=str(resolved_target),
            )

        resolved_target.parent.mkdir(parents=True, exist_ok=True)
        resolved_target.write_bytes(payload)
        return {
            "entry": self._scope.describe_entry(resolved_root, resolved_target),
            "write_mode": mode,
            "before_size_bytes": len(existing),
            "after_size_bytes": len(payload),
            "offset": offset,
        }

    def copy_binary(
        self,
        root: str | Path | None,
        source: str | Path,
        destination: str | Path,
    ) -> dict[str, Any]:
        """Copy a binary file without text decoding."""

        resolved_root, resolved_source = self._scope.resolve_target(root, source)
        _, resolved_destination = self._scope.resolve_target(root, destination)
        if not resolved_source.exists():
            raise NotFoundError(
                code="binary_source_missing",
                message="Binary source does not exist.",
                details={"source": str(resolved_source)},
                path=str(resolved_source),
            )
        resolved_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(resolved_source, resolved_destination)
        return {
            "source": self._scope.describe_entry(resolved_root, resolved_source),
            "destination": self._scope.describe_entry(
                resolved_root, resolved_destination
            ),
            "copied": True,
            "size_bytes": resolved_destination.stat().st_size,
        }

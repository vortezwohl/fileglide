"""Size-related filesystem helpers."""

from __future__ import annotations

from pathlib import Path

from fileglide.exceptions import NotFoundError
from fileglide.services.scope import ScopeService


class SizingService:
    """Report file sizes and aggregated directory sizes."""

    def __init__(self, scope_service: ScopeService) -> None:
        self._scope = scope_service

    def stat_size(
        self, root: str | Path | None, target: str | Path
    ) -> dict[str, object]:
        """Return file size or aggregated directory size for a scoped target."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        if not resolved_target.exists():
            raise NotFoundError(
                code="target_missing",
                message="Target does not exist.",
                details={"target": str(resolved_target)},
                path=str(resolved_target),
            )

        if resolved_target.is_file():
            size_bytes = resolved_target.stat().st_size
            aggregate = False
        else:
            size_bytes = sum(
                entry.stat().st_size
                for entry in resolved_target.rglob("*")
                if entry.is_file()
            )
            aggregate = True

        return {
            "entry": self._scope.describe_entry(resolved_root, resolved_target),
            "size_bytes": size_bytes,
            "aggregate": aggregate,
        }

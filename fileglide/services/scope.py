"""Path normalization and scope enforcement helpers."""

from __future__ import annotations

from pathlib import Path

from fileglide.exceptions import ScopeError


class ScopeService:
    """Resolve user paths and keep operations inside an allowed root."""

    @staticmethod
    def normalize_root(root: str | Path | None) -> Path:
        """Resolve the configured root path without requiring prior existence."""

        base = Path(root) if root is not None else Path.cwd()
        return base.expanduser().resolve(strict=False)

    def resolve_target(
        self, root: str | Path | None, target: str | Path
    ) -> tuple[Path, Path]:
        """Resolve a target path and verify that it stays within the root scope."""

        resolved_root = self.normalize_root(root)
        raw_target = Path(target)
        if raw_target.is_absolute():
            resolved_target = raw_target.expanduser().resolve(strict=False)
        else:
            resolved_target = (
                (resolved_root / raw_target).expanduser().resolve(strict=False)
            )
        self.ensure_within_root(resolved_root, resolved_target)
        return resolved_root, resolved_target

    @staticmethod
    def ensure_within_root(root: Path, target: Path) -> None:
        """Raise when a resolved target escapes the resolved root."""

        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ScopeError(
                code="scope_violation",
                message="Target escapes the configured root scope.",
                details={"root": str(root), "target": str(target)},
                path=str(target),
            ) from exc

    @staticmethod
    def describe_entry(root: Path, target: Path) -> dict[str, object]:
        """Build normalized metadata for a filesystem entry."""

        exists = target.exists()
        if target.is_file():
            kind = "file"
        elif target.is_dir():
            kind = "directory"
        else:
            kind = "missing"

        try:
            relative_path = str(target.relative_to(root))
        except ValueError:
            relative_path = target.name

        return {
            "path": str(target),
            "relative_path": relative_path.replace("\\", "/"),
            "name": target.name,
            "kind": kind,
            "exists": exists,
        }

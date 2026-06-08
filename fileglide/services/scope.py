"""Path resolution helpers and root scope enforcement."""

from __future__ import annotations

from pathlib import Path

from fileglide.exceptions import ScopeError


class ScopeService:
    """Resolve command paths while enforcing root scope constraints."""

    @staticmethod
    def normalize_root(root: str | Path | None) -> Path:
        """Resolve the root directory used by a command."""

        base = Path(root) if root is not None else Path.cwd()
        return base.expanduser().resolve(strict=False)

    def resolve_target(
        self, root: str | Path | None, target: str | Path
    ) -> tuple[Path, Path]:
        """Resolve a target path and ensure it remains inside its root."""

        resolved_root, resolved_target = self._resolve_against_root(root, target)
        self.ensure_within_root(resolved_root, resolved_target)
        return resolved_root, resolved_target

    def resolve_move_pair(
        self,
        source_root: str | Path | None,
        source: str | Path,
        destination_root: str | Path | None,
        destination: str | Path,
    ) -> tuple[Path, Path, Path, Path]:
        """Resolve move sources and destinations, including controlled cross-root moves."""

        resolved_source_root, resolved_source = self.resolve_target(source_root, source)
        actual_destination_root = destination_root
        if actual_destination_root is None:
            actual_destination_root = source_root
        resolved_destination_root, resolved_destination = self.resolve_target(
            actual_destination_root,
            destination,
        )
        return (
            resolved_source_root,
            resolved_source,
            resolved_destination_root,
            resolved_destination,
        )

    @staticmethod
    def ensure_within_root(root: Path, target: Path) -> None:
        """Raise a structured error when a target escapes its root."""

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

    def _resolve_against_root(
        self, root: str | Path | None, target: str | Path
    ) -> tuple[Path, Path]:
        """Resolve an absolute target path against a given root."""

        resolved_root = self.normalize_root(root)
        raw_target = Path(target)
        if raw_target.is_absolute():
            resolved_target = raw_target.expanduser().resolve(strict=False)
        else:
            resolved_target = (
                (resolved_root / raw_target).expanduser().resolve(strict=False)
            )
        return resolved_root, resolved_target

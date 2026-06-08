"""Filesystem traversal helpers with scope and filtering controls."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable

from fileglide.exceptions import NotFoundError, ValidationError
from fileglide.services.scope import ScopeService


class TraversalService:
    """Traverse files and directories with recursion and depth control."""

    def __init__(self, scope_service: ScopeService) -> None:
        self._scope = scope_service

    def list_entries(
        self,
        root: str | Path | None,
        *,
        start: str | Path = ".",
        kind: str = "all",
        recursive: bool = False,
        max_depth: int | None = None,
        include: Iterable[str] = (),
        exclude: Iterable[str] = (),
    ) -> dict[str, object]:
        """List scoped filesystem entries filtered by kind and glob patterns."""

        if kind not in {"all", "file", "directory"}:
            raise ValidationError(
                code="invalid_kind",
                message="Traversal kind must be all, file, or directory.",
                details={"kind": kind},
            )

        resolved_root, resolved_start = self._scope.resolve_target(root, start)
        if not resolved_start.exists():
            raise NotFoundError(
                code="start_missing",
                message="Traversal start path does not exist.",
                details={"start": str(resolved_start)},
                path=str(resolved_start),
            )

        include_patterns = tuple(include)
        exclude_patterns = tuple(exclude)
        entries: list[dict[str, object]] = []
        if resolved_start.is_file():
            if kind in {"all", "file"} and self._matches_filters(
                resolved_root,
                resolved_start,
                include_patterns,
                exclude_patterns,
            ):
                entries.append(
                    self._entry_record(resolved_root, resolved_start, depth=0)
                )
        else:
            if kind in {"all", "directory"} and self._matches_filters(
                resolved_root,
                resolved_start,
                include_patterns,
                exclude_patterns,
            ):
                entries.append(
                    self._entry_record(resolved_root, resolved_start, depth=0)
                )
            for entry in sorted(
                resolved_start.iterdir(), key=lambda item: item.name.casefold()
            ):
                entries.extend(
                    self._walk(
                        root=resolved_root,
                        entry=entry,
                        kind=kind,
                        recursive=recursive,
                        max_depth=max_depth,
                        include=include_patterns,
                        exclude=exclude_patterns,
                        depth=1,
                    )
                )

        return {
            "entries": entries,
            "scope": {
                "root": str(resolved_root),
                "start": str(resolved_start),
                "recursive": recursive,
                "max_depth": max_depth,
                "include": list(include_patterns),
                "exclude": list(exclude_patterns),
                "kind": kind,
            },
            "count": len(entries),
        }

    def _walk(
        self,
        *,
        root: Path,
        entry: Path,
        kind: str,
        recursive: bool,
        max_depth: int | None,
        include: tuple[str, ...],
        exclude: tuple[str, ...],
        depth: int,
    ) -> list[dict[str, object]]:
        if max_depth is not None and depth > max_depth:
            return []

        records: list[dict[str, object]] = []
        if self._is_kind_match(entry, kind) and self._matches_filters(
            root, entry, include, exclude
        ):
            records.append(self._entry_record(root, entry, depth=depth))

        if entry.is_dir() and recursive:
            for child in sorted(entry.iterdir(), key=lambda item: item.name.casefold()):
                records.extend(
                    self._walk(
                        root=root,
                        entry=child,
                        kind=kind,
                        recursive=recursive,
                        max_depth=max_depth,
                        include=include,
                        exclude=exclude,
                        depth=depth + 1,
                    )
                )
        return records

    @staticmethod
    def _is_kind_match(entry: Path, kind: str) -> bool:
        if kind == "all":
            return True
        if kind == "file":
            return entry.is_file()
        return entry.is_dir()

    @staticmethod
    def _matches_filters(
        root: Path,
        entry: Path,
        include: tuple[str, ...],
        exclude: tuple[str, ...],
    ) -> bool:
        relative_path = str(entry.relative_to(root)).replace("\\", "/")
        if include and not any(
            fnmatch(relative_path, pattern) or fnmatch(entry.name, pattern)
            for pattern in include
        ):
            return False
        if exclude and any(
            fnmatch(relative_path, pattern) or fnmatch(entry.name, pattern)
            for pattern in exclude
        ):
            return False
        return True

    def _entry_record(
        self, root: Path, entry: Path, *, depth: int
    ) -> dict[str, object]:
        metadata = self._scope.describe_entry(root, entry)
        size_bytes = entry.stat().st_size if entry.is_file() else 0
        return {**metadata, "depth": depth, "size_bytes": size_bytes}

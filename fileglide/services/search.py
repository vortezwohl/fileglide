"""Path and content search helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from vortezwohl.nlp import LevenshteinDistance

from fileglide.exceptions import ValidationError
from fileglide.services.encoding import EncodingService
from fileglide.services.scope import ScopeService
from fileglide.services.traversal import TraversalService


class SearchService:
    """Search file names, paths, and text content within a scope."""

    def __init__(
        self,
        scope_service: ScopeService,
        traversal_service: TraversalService,
        encoding_service: EncodingService,
    ) -> None:
        self._scope = scope_service
        self._traversal = traversal_service
        self._encoding = encoding_service
        self._distance = LevenshteinDistance(ignore_case=True)

    def search_names(
        self,
        root: str | Path | None,
        *,
        query: str,
        mode: str,
        start: str | Path = ".",
        kind: str = "all",
        recursive: bool = True,
        max_depth: int | None = None,
        include: Iterable[str] = (),
        exclude: Iterable[str] = (),
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search names and relative paths using exact, contains, or fuzzy matching."""

        traversal = self._traversal.list_entries(
            root,
            start=start,
            kind=kind,
            recursive=recursive,
            max_depth=max_depth,
            include=include,
            exclude=exclude,
        )
        entries = traversal["entries"]
        normalized_query = query.casefold()

        if mode == "exact":
            matches = [
                {**entry, "score": 0}
                for entry in entries
                if entry["name"].casefold() == normalized_query
                or str(entry["relative_path"]).casefold() == normalized_query
            ]
        elif mode == "contains":
            matches = [
                {**entry, "score": 0}
                for entry in entries
                if normalized_query in entry["name"].casefold()
                or normalized_query in str(entry["relative_path"]).casefold()
            ]
        elif mode == "fuzzy":
            scored = []
            for entry in entries:
                score_name = self._distance(query, entry["name"])
                score_path = self._distance(query, str(entry["relative_path"]))
                score = min(score_name, score_path)
                scored.append({**entry, "score": score})
            matches = sorted(
                scored, key=lambda item: (item["score"], item["relative_path"])
            )
        else:
            raise ValidationError(
                code="invalid_search_mode",
                message="Search mode must be exact, contains, or fuzzy.",
                details={"mode": mode},
            )

        return {
            "query": query,
            "mode": mode,
            "count": len(matches[:limit]),
            "matches": matches[:limit],
            "scope": traversal["scope"],
        }

    def regex_search(
        self,
        root: str | Path | None,
        *,
        pattern: str,
        start: str | Path = ".",
        recursive: bool = True,
        max_depth: int | None = None,
        include: Iterable[str] = (),
        exclude: Iterable[str] = (),
        encoding: str | None = None,
    ) -> dict[str, Any]:
        """Search text file content with a regular expression."""

        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise ValidationError(
                code="invalid_regex",
                message="The supplied regular expression is invalid.",
                details={"pattern": pattern, "reason": str(exc)},
            ) from exc

        traversal = self._traversal.list_entries(
            root,
            start=start,
            kind="file",
            recursive=recursive,
            max_depth=max_depth,
            include=include,
            exclude=exclude,
        )
        hits = []
        for entry in traversal["entries"]:
            path = Path(entry["path"])
            if self._encoding.is_binary_path(path):
                continue
            info = self._encoding.ensure_text(path, explicit_encoding=encoding)
            for line_number, line in enumerate(info["text"].splitlines(), start=1):
                match = compiled.search(line)
                if match:
                    hits.append(
                        {
                            "path": str(path),
                            "relative_path": entry["relative_path"],
                            "line_number": line_number,
                            "preview": line,
                            "match": match.group(0),
                            "span": list(match.span()),
                            "encoding": info["encoding"],
                        }
                    )

        return {
            "pattern": pattern,
            "count": len(hits),
            "matches": hits,
            "scope": traversal["scope"],
        }

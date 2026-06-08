"""Text read, write, and precise editing workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fileglide.exceptions import NotFoundError, ValidationError
from fileglide.services.encoding import EncodingService
from fileglide.services.scope import ScopeService


class TextService:
    """Read and edit text files with explicit metadata reporting."""

    def __init__(
        self, scope_service: ScopeService, encoding_service: EncodingService
    ) -> None:
        self._scope = scope_service
        self._encoding = encoding_service

    def read_text(
        self,
        root: str | Path | None,
        target: str | Path,
        *,
        encoding: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> dict[str, Any]:
        """Read a full text file or a selected line range."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        if not resolved_target.exists():
            raise NotFoundError(
                code="text_missing",
                message="Text target does not exist.",
                details={"target": str(resolved_target)},
                path=str(resolved_target),
            )
        info = self._encoding.ensure_text(resolved_target, explicit_encoding=encoding)
        lines = info["text"].splitlines()

        if start_line is None and end_line is None:
            selected_text = info["text"]
            selected_lines = [
                {"line_number": index + 1, "text": line}
                for index, line in enumerate(lines)
            ]
            range_info = None
        else:
            start = start_line or 1
            end = end_line or len(lines)
            if start < 1 or end < start:
                raise ValidationError(
                    code="invalid_line_range",
                    message="Line range must be positive and ordered.",
                    details={"start_line": start_line, "end_line": end_line},
                    path=str(resolved_target),
                )
            selected = lines[start - 1 : end]
            selected_text = "\n".join(selected)
            selected_lines = [
                {"line_number": start + index, "text": line}
                for index, line in enumerate(selected)
            ]
            range_info = {"start_line": start, "end_line": end}

        return {
            "entry": self._scope.describe_entry(resolved_root, resolved_target),
            "content": selected_text,
            "lines": selected_lines,
            "line_count": len(lines),
            "selection": range_info,
            "encoding": {
                "name": info["encoding"],
                "bom": info.get("bom", False),
                "source": info.get("source"),
                "confidence": info.get("confidence"),
            },
        }

    def write_text(
        self,
        root: str | Path | None,
        target: str | Path,
        *,
        content: str,
        mode: str = "overwrite",
        encoding: str | None = None,
        position: int | None = None,
    ) -> dict[str, Any]:
        """Write text by overwrite, append, or insert mode."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        existed = resolved_target.exists()
        previous_info = None
        previous_text = ""
        if existed:
            previous_info = self._encoding.ensure_text(
                resolved_target, explicit_encoding=encoding
            )
            previous_text = previous_info["text"]

        target_encoding = self._encoding.encoding_for_write(
            existing_encoding=previous_info["encoding"] if previous_info else None,
            requested_encoding=encoding,
        )

        if mode == "overwrite":
            new_text = content
        elif mode == "append":
            new_text = previous_text + content
        elif mode == "insert":
            insert_at = len(previous_text) if position is None else position
            if insert_at < 0 or insert_at > len(previous_text):
                raise ValidationError(
                    code="invalid_insert_position",
                    message="Insert position is out of bounds.",
                    details={"position": position, "length": len(previous_text)},
                    path=str(resolved_target),
                )
            new_text = previous_text[:insert_at] + content + previous_text[insert_at:]
        else:
            raise ValidationError(
                code="invalid_write_mode",
                message="Write mode must be overwrite, append, or insert.",
                details={"mode": mode},
                path=str(resolved_target),
            )

        validation = self._encoding.validate_round_trip(new_text, target_encoding)
        resolved_target.parent.mkdir(parents=True, exist_ok=True)
        resolved_target.write_text(new_text, encoding=target_encoding, newline="")

        return {
            "entry": self._scope.describe_entry(resolved_root, resolved_target),
            "write_mode": mode,
            "encoding": validation,
            "before_size_bytes": len(previous_text.encode(target_encoding))
            if existed
            else 0,
            "after_size_bytes": validation["size_bytes"],
            "insert_position": position,
        }

    def replace_lines(
        self,
        root: str | Path | None,
        target: str | Path,
        *,
        start_line: int,
        end_line: int,
        content: str,
        encoding: str | None = None,
    ) -> dict[str, Any]:
        """Replace a specific line range in a text file."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        info = self._encoding.ensure_text(resolved_target, explicit_encoding=encoding)
        lines = info["text"].splitlines(keepends=True)
        if start_line < 1 or end_line < start_line or end_line > len(lines):
            raise ValidationError(
                code="invalid_line_range",
                message="Line range is outside the file bounds.",
                details={
                    "start_line": start_line,
                    "end_line": end_line,
                    "line_count": len(lines),
                },
                path=str(resolved_target),
            )

        replacement_lines = content.splitlines(keepends=True)
        if content and not content.endswith(("\n", "\r")):
            replacement_lines[-1] = replacement_lines[-1]
        new_lines = lines[: start_line - 1] + replacement_lines + lines[end_line:]
        new_text = "".join(new_lines)
        target_encoding = self._encoding.encoding_for_write(
            existing_encoding=info["encoding"],
            requested_encoding=encoding,
        )
        validation = self._encoding.validate_round_trip(new_text, target_encoding)
        resolved_target.write_text(new_text, encoding=target_encoding, newline="")

        return {
            "entry": self._scope.describe_entry(resolved_root, resolved_target),
            "changed_range": {"start_line": start_line, "end_line": end_line},
            "encoding": validation,
            "replacement_line_count": len(replacement_lines),
        }

    def insert_by_anchor(
        self,
        root: str | Path | None,
        target: str | Path,
        *,
        anchor: str,
        content: str,
        before: bool = False,
        encoding: str | None = None,
    ) -> dict[str, Any]:
        """Insert content before or after a unique anchor string."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        info = self._encoding.ensure_text(resolved_target, explicit_encoding=encoding)
        matches = info["text"].count(anchor)
        if matches != 1:
            raise ValidationError(
                code="anchor_resolution_failed",
                message="Anchor must resolve to exactly one match.",
                details={"anchor": anchor, "matches": matches},
                path=str(resolved_target),
            )

        position = info["text"].index(anchor)
        if not before:
            position += len(anchor)
        return self.write_text(
            root,
            target,
            content=content,
            mode="insert",
            encoding=encoding,
            position=position,
        )

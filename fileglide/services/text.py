"""Text read, write, and precise editing workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fileglide.exceptions import NotFoundError, ValidationError
from fileglide.services.encoding import EncodingService
from fileglide.services.scope import ScopeService


@dataclass(slots=True)
class TextDocument:
    """Represent a decoded text file together with serialization metadata."""

    text: str
    charset: str
    bom: bool
    newline: str
    final_newline: bool

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        charset: str,
        bom: bool,
        newline: str,
    ) -> TextDocument:
        """Create a document model from decoded text and metadata."""

        return cls(
            text=text,
            charset=charset,
            bom=bom,
            newline=newline,
            final_newline=bool(text) and text.endswith(("\n", "\r")),
        )

    def line_entries(self) -> list[tuple[str, str]]:
        """Split the document into logical lines with their trailing endings."""

        entries: list[tuple[str, str]] = []
        text = self.text
        index = 0
        while index < len(text):
            line_end = index
            while line_end < len(text) and text[line_end] not in "\r\n":
                line_end += 1
            line_text = text[index:line_end]
            if line_end >= len(text):
                newline = ""
            elif text[line_end] == "\r" and line_end + 1 < len(text) and text[line_end + 1] == "\n":
                newline = "\r\n"
                line_end += 2
            else:
                newline = text[line_end]
                line_end += 1
            entries.append((line_text, newline))
            index = line_end
        if not entries and not text:
            return []
        return entries

    def replace_range(self, start_line: int, end_line: int, replacement: str) -> TextDocument:
        """Replace a logical line range while preserving surrounding boundaries."""

        entries = self.line_entries()
        if start_line < 1 or end_line < start_line or end_line > len(entries):
            raise ValidationError(
                code="invalid_line_range",
                message="Line range is outside the file bounds.",
                details={
                    "start_line": start_line,
                    "end_line": end_line,
                    "line_count": len(entries),
                },
            )

        replacement_entries = self._parse_replacement_entries(replacement)
        trailing_newline = self._replacement_trailing_newline(entries, start_line, end_line, replacement)
        normalized_entries = self._normalize_replacement_entries(
            replacement_entries,
            trailing_newline=trailing_newline,
        )
        updated_entries = entries[: start_line - 1] + normalized_entries + entries[end_line:]
        return TextDocument.from_text(
            self._entries_to_text(updated_entries),
            charset=self.charset,
            bom=self.bom,
            newline=self.newline,
        )

    def insert_text(self, position: int, content: str) -> TextDocument:
        """Insert content at an absolute character position."""

        if position < 0 or position > len(self.text):
            raise ValidationError(
                code="invalid_insert_position",
                message="Insert position is out of bounds.",
                details={"position": position, "length": len(self.text)},
            )
        return TextDocument.from_text(
            self.text[:position] + content + self.text[position:],
            charset=self.charset,
            bom=self.bom,
            newline=self.newline,
        )

    def append_text(self, content: str) -> TextDocument:
        """Append content to the document."""

        return self.insert_text(len(self.text), content)

    @staticmethod
    def _parse_replacement_entries(replacement: str) -> list[tuple[str, str]]:
        """Parse replacement text into logical line entries."""

        if replacement == "":
            return []
        temp_document = TextDocument.from_text(
            replacement,
            charset="utf-8",
            bom=False,
            newline="\n",
        )
        return temp_document.line_entries()

    def _replacement_trailing_newline(
        self,
        entries: list[tuple[str, str]],
        start_line: int,
        end_line: int,
        replacement: str,
    ) -> str:
        """Decide which newline should terminate the replacement block."""

        if replacement.endswith(("\n", "\r")):
            return ""
        if end_line < len(entries):
            return entries[end_line - 1][1] or self.newline
        return entries[end_line - 1][1]

    def _normalize_replacement_entries(
        self,
        replacement_entries: list[tuple[str, str]],
        *,
        trailing_newline: str,
    ) -> list[tuple[str, str]]:
        """Apply document newline defaults to replacement entries."""

        if not replacement_entries:
            return []
        normalized: list[tuple[str, str]] = []
        for line_text, newline in replacement_entries[:-1]:
            normalized.append((line_text, newline or self.newline))
        last_text, last_newline = replacement_entries[-1]
        normalized.append((last_text, last_newline or trailing_newline))
        return normalized

    @staticmethod
    def _entries_to_text(entries: list[tuple[str, str]]) -> str:
        """Join logical line entries into a text buffer."""

        return "".join(line_text + newline for line_text, newline in entries)


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
        content_source: dict[str, Any] | None = None,
        mode: str = "overwrite",
        encoding: str | None = None,
        position: int | None = None,
    ) -> dict[str, Any]:
        """Write text by overwrite, append, or insert mode."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        existed = resolved_target.exists()
        document = self._load_document(resolved_target, explicit_encoding=encoding)
        before_size_bytes = document["size_bytes"] if existed else 0

        if mode == "overwrite":
            updated_document = TextDocument.from_text(
                content,
                charset=document["model"].charset,
                bom=document["model"].bom,
                newline=document["model"].newline,
            )
        elif mode == "append":
            updated_document = document["model"].append_text(content)
        elif mode == "insert":
            insert_at = len(document["model"].text) if position is None else position
            updated_document = document["model"].insert_text(insert_at, content)
        else:
            raise ValidationError(
                code="invalid_write_mode",
                message="Write mode must be overwrite, append, or insert.",
                details={"mode": mode},
                path=str(resolved_target),
            )

        write_result = self._persist_document(
            resolved_root,
            resolved_target,
            original=document,
            updated=updated_document,
            content_source=content_source,
        )
        write_result["write_mode"] = mode
        write_result["before_size_bytes"] = before_size_bytes
        write_result["insert_position"] = position
        return write_result

    def replace_lines(
        self,
        root: str | Path | None,
        target: str | Path,
        *,
        start_line: int,
        end_line: int,
        content: str,
        content_source: dict[str, Any] | None = None,
        encoding: str | None = None,
    ) -> dict[str, Any]:
        """Replace a specific line range in a text file."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        document = self._load_document(resolved_target, explicit_encoding=encoding)
        updated_document = document["model"].replace_range(start_line, end_line, content)
        result = self._persist_document(
            resolved_root,
            resolved_target,
            original=document,
            updated=updated_document,
            content_source=content_source,
        )
        result["changed_range"] = {"start_line": start_line, "end_line": end_line}
        result["replacement_line_count"] = len(content.splitlines()) if content else 0
        return result

    def insert_by_anchor(
        self,
        root: str | Path | None,
        target: str | Path,
        *,
        anchor: str,
        content: str,
        content_source: dict[str, Any] | None = None,
        before: bool = False,
        encoding: str | None = None,
    ) -> dict[str, Any]:
        """Insert content before or after a unique anchor string."""

        resolved_root, resolved_target = self._scope.resolve_target(root, target)
        document = self._load_document(resolved_target, explicit_encoding=encoding)
        matches = document["model"].text.count(anchor)
        if matches != 1:
            raise ValidationError(
                code="anchor_resolution_failed",
                message="Anchor must resolve to exactly one match.",
                details={"anchor": anchor, "matches": matches},
                path=str(resolved_target),
            )

        position = document["model"].text.index(anchor)
        if not before:
            position += len(anchor)
        updated_document = document["model"].insert_text(position, content)
        result = self._persist_document(
            resolved_root,
            resolved_target,
            original=document,
            updated=updated_document,
            content_source=content_source,
        )
        result["anchor"] = {"value": anchor, "matches": matches, "before": before}
        result["write_mode"] = "insert"
        result["insert_position"] = position
        return result

    def _load_document(
        self, path: Path, *, explicit_encoding: str | None = None
    ) -> dict[str, Any]:
        """Load a text document and its write policy metadata."""

        if not path.exists():
            model = TextDocument.from_text(
                "",
                charset=explicit_encoding or "utf-8",
                bom=False,
                newline="\n",
            )
            return {
                "model": model,
                "size_bytes": 0,
                "encoding": explicit_encoding or "utf-8",
                "bom": False,
                "newline": "\n",
                "policy": self._encoding.resolve_write_policy(
                    existing_encoding=None,
                    existing_bom=False,
                    existing_newline=None,
                    requested_encoding=explicit_encoding,
                ),
            }

        info = self._encoding.ensure_text(path, explicit_encoding=explicit_encoding)
        newline = self._encoding.detect_newline(info["text"])
        policy = self._encoding.resolve_write_policy(
            existing_encoding=info["encoding"],
            existing_bom=info.get("bom", False),
            existing_newline=newline,
            requested_encoding=explicit_encoding,
        )
        model = TextDocument.from_text(
            info["text"],
            charset=policy["charset"],
            bom=policy["bom"],
            newline=policy["newline"],
        )
        return {
            "model": model,
            "size_bytes": info.get("size_bytes", 0),
            "encoding": info["encoding"],
            "bom": info.get("bom", False),
            "newline": newline,
            "policy": policy,
        }

    def _persist_document(
        self,
        resolved_root: Path,
        resolved_target: Path,
        *,
        original: dict[str, Any],
        updated: TextDocument,
        content_source: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Serialize, write, and verify the updated text document."""

        policy = original["policy"]
        updated = TextDocument.from_text(
            updated.text,
            charset=policy["charset"],
            bom=policy["bom"],
            newline=policy["newline"],
        )
        payload = self._encoding.serialize_text(
            updated.text,
            charset=updated.charset,
            bom=updated.bom,
        )
        verification = self._encoding.verify_serialized_bytes(
            updated.text,
            payload,
            charset=updated.charset,
            bom=updated.bom,
        )
        self._encoding.atomic_write_bytes(resolved_target, payload)
        written_bytes = resolved_target.read_bytes()
        if written_bytes != payload:
            raise ValidationError(
                code="write_verification_failed",
                message="The final file bytes differ from the serialized payload.",
                details={"target": str(resolved_target)},
                path=str(resolved_target),
            )

        return {
            "entry": self._scope.describe_entry(resolved_root, resolved_target),
            "content_source": content_source or {"source": "inline"},
            "encoding": {
                "name": updated.charset,
                "bom": updated.bom,
                "newline": updated.newline,
                "policy": policy,
            },
            "verification": verification,
            "after_size_bytes": len(payload),
        }

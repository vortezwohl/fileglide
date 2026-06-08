"""Facade that coordinates fileglide domain services."""

from __future__ import annotations

from inspect import signature
from typing import Any, Callable

from fileglide.exceptions import ValidationError
from fileglide.models import PreviewDetail
from fileglide.services.batch import BatchService
from fileglide.services.binary import BinaryService
from fileglide.services.encoding import EncodingService
from fileglide.services.filesystem import FilesystemService
from fileglide.services.scope import ScopeService
from fileglide.services.search import SearchService
from fileglide.services.sizing import SizingService
from fileglide.services.text import TextService
from fileglide.services.traversal import TraversalService


class FileGlideFacade:
    """Expose high-level operations for CLI commands and batch plans."""

    def __init__(self) -> None:
        self.scope = ScopeService()
        self.encoding = EncodingService()
        self.filesystem = FilesystemService(self.scope)
        self.traversal = TraversalService(self.scope)
        self.sizing = SizingService(self.scope)
        self.text = TextService(self.scope, self.encoding)
        self.binary = BinaryService(self.scope)
        self.search = SearchService(self.scope, self.traversal, self.encoding)
        self.batch = BatchService()
        self._batch_actions: dict[str, Callable[..., dict[str, Any]]] = {
            "file.create": self.filesystem.create_file,
            "file.delete": self.filesystem.delete_file,
            "path.create": self.filesystem.create_path,
            "path.delete": self.filesystem.delete_path,
            "text.write": self.text.write_text,
            "text.replace-lines": self.text.replace_lines,
            "binary.write": self.binary.write_bytes,
            "binary.copy": self.binary.copy_binary,
        }

    def run_batch_step(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a single batch step by action identifier."""

        operation = self._get_batch_action(action)
        return operation(**arguments)

    def preview_batch_step(
        self, action: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Return a structured preview for a batch step without
        mutating the filesystem."""

        operation = self._get_batch_action(action)
        self._bind_batch_arguments(action, operation, arguments)
        affected_targets = [
            str(value)
            for key, value in arguments.items()
            if key in {"target", "source", "destination"}
        ]
        preview = PreviewDetail(
            action=action,
            dry_run=True,
            destructive=True,
            requires_confirmation=True,
            confirmed=False,
            affected_targets=affected_targets,
            details={"arguments": arguments},
        )
        return {"ok": True, "preview": preview}

    def _get_batch_action(self, action: str) -> Callable[..., dict[str, Any]]:
        if action not in self._batch_actions:
            raise ValidationError(
                code="unsupported_batch_action",
                message="The batch step action is not supported.",
                details={"action": action},
            )
        return self._batch_actions[action]

    @staticmethod
    def _bind_batch_arguments(
        action: str,
        operation: Callable[..., dict[str, Any]],
        arguments: dict[str, Any],
    ) -> None:
        try:
            signature(operation).bind(**arguments)
        except TypeError as exc:
            raise ValidationError(
                code="invalid_batch_arguments",
                message="Batch step arguments do not match the target operation.",
                details={"action": action, "reason": str(exc)},
            ) from exc

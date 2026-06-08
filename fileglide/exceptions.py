"""Domain exceptions for predictable CLI failure handling."""

from __future__ import annotations

from typing import Any

from fileglide.models import ErrorDetail


class FileGlideError(Exception):
    """Base exception carrying structured failure metadata."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        path: str | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.path = path
        self.exit_code = exit_code

    def to_error_detail(self) -> ErrorDetail:
        """Convert the exception into a response error payload."""

        return ErrorDetail(
            code=self.code,
            message=self.message,
            details=self.details,
            path=self.path,
        )


class ValidationError(FileGlideError):
    """Raised when command input or plan data is invalid."""


class ScopeError(FileGlideError):
    """Raised when a target escapes the configured root scope."""


class NotFoundError(FileGlideError):
    """Raised when a requested filesystem entry does not exist."""


class AlreadyExistsError(FileGlideError):
    """Raised when a creation target already exists unexpectedly."""


class ConfirmRequiredError(FileGlideError):
    """Raised when a destructive action requires explicit confirmation."""


class BinaryTextMismatchError(FileGlideError):
    """Raised when a text command is applied to binary content or the reverse."""


class EncodingRiskError(FileGlideError):
    """Raised when a write cannot be completed losslessly."""

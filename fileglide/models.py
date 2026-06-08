"""Structured response models used by fileglide commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fileglide.serializers import to_primitive


@dataclass(slots=True)
class ErrorDetail:
    """Represent a machine-readable command error."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    path: str | None = None


@dataclass(slots=True)
class WarningDetail:
    """Represent a machine-readable command warning."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    path: str | None = None


@dataclass(slots=True)
class PreviewDetail:
    """Describe a potentially destructive operation before execution."""

    action: str
    dry_run: bool
    destructive: bool
    requires_confirmation: bool
    confirmed: bool
    affected_targets: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OperationResponse:
    """Represent the stable top-level JSON contract returned by commands."""

    ok: bool
    operation: str
    targets: list[str] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    errors: list[ErrorDetail | dict[str, Any]] = field(default_factory=list)
    warnings: list[WarningDetail | dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the response into a JSON-safe dictionary."""

        return to_primitive(
            {
                "ok": self.ok,
                "operation": self.operation,
                "targets": self.targets,
                "result": self.result,
                "errors": self.errors,
                "warnings": self.warnings,
                "meta": self.meta,
            }
        )

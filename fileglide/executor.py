"""Command execution and response rendering helpers."""

from __future__ import annotations

import json
from typing import Any, Callable

import click

from fileglide.exceptions import FileGlideError
from fileglide.models import OperationResponse


class CommandExecutor:
    """Run command handlers and emit stable output."""

    def __init__(self, context: Any) -> None:
        self._context = context

    def execute(
        self,
        operation: str,
        targets: list[str],
        handler: Callable[[], dict[str, Any] | OperationResponse],
        *,
        meta: dict[str, Any] | None = None,
        render: bool = True,
    ) -> OperationResponse:
        """Execute a handler and wrap its outcome in the response contract."""

        try:
            payload = handler()
            if isinstance(payload, OperationResponse):
                response = payload
            else:
                response = OperationResponse(
                    ok=True,
                    operation=operation,
                    targets=targets,
                    result=payload,
                    meta=meta or {},
                )
        except FileGlideError as exc:
            response = OperationResponse(
                ok=False,
                operation=operation,
                targets=targets,
                result={},
                errors=[exc.to_error_detail()],
                meta=meta or {},
            )
        except Exception as exc:  # pragma: no cover
            response = OperationResponse(
                ok=False,
                operation=operation,
                targets=targets,
                result={},
                errors=[
                    {
                        "code": "internal_error",
                        "message": str(exc),
                        "details": {"exception_type": exc.__class__.__name__},
                        "path": None,
                    }
                ],
                meta=meta or {},
            )

        if render:
            self.render(response)
            if not response.ok:
                raise click.exceptions.Exit(code=1)
        return response

    def render(self, response: OperationResponse) -> None:
        """Emit the response using the configured output format."""

        if self._context.output_format == "json":
            indent = 2 if self._context.pretty else None
            click.echo(
                json.dumps(response.to_dict(), ensure_ascii=False, indent=indent)
            )
            return

        click.echo(self._render_text(response))

    @staticmethod
    def _render_text(response: OperationResponse) -> str:
        """Render a compact human-readable fallback output."""

        lines = [f"ok={response.ok}", f"operation={response.operation}"]
        if response.targets:
            lines.append(f"targets={', '.join(response.targets)}")
        if response.result:
            lines.append(f"result={response.result}")
        if response.warnings:
            lines.append(f"warnings={len(response.warnings)}")
        if response.errors:
            lines.append(f"errors={len(response.errors)}")
        return "\n".join(lines)

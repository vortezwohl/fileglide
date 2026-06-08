"""Shared click helpers for command modules."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Callable
from typing import Any

import click

from fileglide.exceptions import EncodingRiskError, NotFoundError, ValidationError
from fileglide.runtime import RuntimeState


CommandDecorator = Callable[[Callable[..., Any]], Callable[..., Any]]
pass_runtime = click.make_pass_decorator(RuntimeState)


def root_option(func: Callable[..., Any]) -> Callable[..., Any]:
    """Add the common root option to a click command."""

    return click.option(
        "--root",
        type=click.Path(path_type=str),
        default=None,
        help="Scope root used to resolve relative targets.",
    )(func)


def destructive_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Add shared destructive operation flags."""

    decorated = click.option(
        "--confirm",
        is_flag=True,
        default=False,
        help="Confirm a destructive operation.",
    )(func)
    return click.option(
        "--dry-run",
        is_flag=True,
        default=False,
        help="Preview the operation without mutating the filesystem.",
    )(decorated)


def traversal_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Add shared traversal-related options."""

    decorated = click.option(
        "--recursive/--no-recursive",
        default=True,
        help="Enable or disable recursive traversal.",
    )(func)
    decorated = click.option(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum traversal depth relative to the start path.",
    )(decorated)
    decorated = click.option(
        "--exclude",
        multiple=True,
        help="Glob pattern used to exclude matching entries.",
    )(decorated)
    return click.option(
        "--include",
        multiple=True,
        help="Glob pattern used to include matching entries.",
    )(decorated)


def text_content_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Add shared text content source options."""

    decorated = click.option(
        "--content-stdin",
        is_flag=True,
        default=False,
        help="Read text content from stdin bytes.",
    )(func)
    decorated = click.option(
        "--content-file",
        type=click.Path(path_type=str),
        default=None,
        help="Read text content from a file path.",
    )(decorated)
    return click.option(
        "--content",
        default=None,
        help="Inline text content to write.",
    )(decorated)


def binary_content_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Add shared binary content source options."""

    decorated = click.option(
        "--data-stdin",
        is_flag=True,
        default=False,
        help="Read binary data from stdin.",
    )(func)
    decorated = click.option(
        "--data-file",
        type=click.Path(path_type=str),
        default=None,
        help="Read binary data from a file path.",
    )(decorated)
    return click.option(
        "--data-hex",
        default=None,
        help="Hex-encoded binary data.",
    )(decorated)


def resolve_text_content_source(
    runtime: RuntimeState,
    *,
    content: str | None,
    content_file: str | None,
    content_stdin: bool,
) -> tuple[str, dict[str, Any]]:
    """Resolve a single text payload source into content and metadata."""

    source_name, source_value = _resolve_selected_source(
        source_kind="text content",
        sources={
            "inline": content,
            "file": content_file,
            "stdin": content_stdin,
        },
    )
    if source_name == "inline":
        return str(source_value), {"source": "inline"}
    if source_name == "file":
        path = Path(str(source_value)).expanduser().resolve(strict=False)
        if not path.exists():
            raise NotFoundError(
                code="content_file_missing",
                message="The content file does not exist.",
                details={"path": str(path)},
                path=str(path),
            )
        try:
            info = runtime.facade.encoding.ensure_text(path)
        except EncodingRiskError as exc:
            raise ValidationError(
                code="invalid_text_content_source",
                message="The content file is not valid text input.",
                details={"path": str(path), "reason": exc.code},
                path=str(path),
            ) from exc
        return info["text"], {
            "source": "file",
            "path": str(path),
            "encoding": info["encoding"],
            "bom": info.get("bom", False),
        }

    stdin_payload = click.get_binary_stream("stdin").read()
    if runtime.facade.encoding.is_binary_payload(stdin_payload):
        raise ValidationError(
            code="invalid_text_content_source",
            message="Stdin payload appears to be binary, not text.",
            details={"source": "stdin"},
        )
    info = runtime.facade.encoding.detect(stdin_payload)
    return info["text"], {
        "source": "stdin",
        "encoding": info["encoding"],
        "bom": info.get("bom", False),
    }


def resolve_binary_content_source(
    *,
    data_hex: str | None,
    data_file: str | None,
    data_stdin: bool,
) -> tuple[bytes, dict[str, Any]]:
    """Resolve a single binary payload source into bytes and metadata."""

    source_name, source_value = _resolve_selected_source(
        source_kind="binary content",
        sources={"hex": data_hex, "file": data_file, "stdin": data_stdin},
    )
    if source_name == "hex":
        try:
            payload = bytes.fromhex(str(source_value))
        except ValueError as exc:
            raise ValidationError(
                code="invalid_binary_hex",
                message="Binary hex input is not valid hexadecimal data.",
                details={"source": "hex"},
            ) from exc
        return payload, {"source": "hex"}
    if source_name == "file":
        path = Path(str(source_value)).expanduser().resolve(strict=False)
        if not path.exists():
            raise NotFoundError(
                code="binary_data_file_missing",
                message="The binary data file does not exist.",
                details={"path": str(path)},
                path=str(path),
            )
        payload = path.read_bytes()
        return payload, {"source": "file", "path": str(path)}

    payload = click.get_binary_stream("stdin").read()
    return payload, {"source": "stdin"}


def _resolve_selected_source(
    *, source_kind: str, sources: dict[str, object | None]
) -> tuple[str, object]:
    """Validate that exactly one payload source was selected."""

    selected = [
        (name, value)
        for name, value in sources.items()
        if _source_is_selected(value)
    ]
    selected_names = [name for name, _ in selected]
    if len(selected) != 1:
        raise ValidationError(
            code="invalid_content_source_combination",
            message=(
                f"Exactly one {source_kind} source must be provided for this command."
            ),
            details={
                "selected_sources": selected_names,
                "available_sources": list(sources.keys()),
            },
        )
    return selected[0]


def _source_is_selected(value: object | None) -> bool:
    """Determine whether a payload source option counts as selected."""

    if isinstance(value, bool):
        return value
    return value is not None

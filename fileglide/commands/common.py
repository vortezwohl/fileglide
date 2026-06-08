"""Shared click helpers for command modules."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import click

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

"CLI commands for directory lifecycle operations and path search."

from __future__ import annotations

import click

from fileglide.commands.common import (
    destination_root_option,
    destructive_options,
    pass_runtime,
    root_option,
    traversal_options,
)


def create_path_group() -> click.Group:
    """Create the path command group."""

    @click.group("path")
    def path_group() -> None:
        """Manage directories and general path metadata."""

    @path_group.command("create")
    @root_option
    @click.option(
        "--parents/--no-parents",
        default=True,
        help="Create missing parent directories.",
    )
    @click.option(
        "--exist-ok/--fail-if-exists",
        default=True,
        help="Allow the directory to exist already.",
    )
    @click.argument("target")
    @pass_runtime
    def create_command(runtime, root, parents, exist_ok, target) -> None:
        runtime.executor.execute(
            "path.create",
            [target],
            lambda: runtime.facade.filesystem.create_path(
                root, target, parents=parents, exist_ok=exist_ok
            ),
            meta={"root": root},
        )

    @path_group.command("delete")
    @root_option
    @destructive_options
    @click.option(
        "--recursive",
        is_flag=True,
        default=False,
        help="Delete non-empty directories recursively.",
    )
    @click.option(
        "--missing-ok",
        is_flag=True,
        default=False,
        help="Allow deleting a missing directory.",
    )
    @click.argument("target")
    @pass_runtime
    def delete_command(
        runtime, root, dry_run, confirm, recursive, missing_ok, target
    ) -> None:
        runtime.executor.execute(
            "path.delete",
            [target],
            lambda: runtime.facade.filesystem.delete_path(
                root,
                target,
                recursive=recursive,
                dry_run=dry_run,
                confirm=confirm,
                missing_ok=missing_ok,
            ),
            meta={"root": root, "dry_run": dry_run},
        )

    @path_group.command("move")
    @root_option
    @destination_root_option
    @destructive_options
    @click.argument("source")
    @click.argument("destination")
    @pass_runtime
    def move_command(
        runtime, root, to_root, dry_run, confirm, source, destination
    ) -> None:
        runtime.executor.execute(
            "path.move",
            [source, destination],
            lambda: runtime.facade.filesystem.move_path(
                root,
                source,
                destination,
                destination_root=to_root,
                dry_run=dry_run,
                confirm=confirm,
            ),
            meta={"root": root, "to_root": to_root, "dry_run": dry_run},
        )

    @path_group.command("exists")
    @root_option
    @click.argument("target")
    @pass_runtime
    def exists_command(runtime, root, target) -> None:
        runtime.executor.execute(
            "path.exists",
            [target],
            lambda: runtime.facade.filesystem.exists(root, target),
            meta={"root": root},
        )

    @path_group.command("list")
    @root_option
    @traversal_options
    @click.option(
        "--kind",
        type=click.Choice(["all", "directory"], case_sensitive=False),
        default="directory",
        show_default=True,
        help="Path entry kind to return.",
    )
    @click.argument("start", default=".")
    @pass_runtime
    def list_command(
        runtime, root, include, exclude, max_depth, recursive, kind, start
    ) -> None:
        runtime.executor.execute(
            "path.list",
            [start],
            lambda: runtime.facade.traversal.list_entries(
                root,
                start=start,
                kind=kind,
                recursive=recursive,
                max_depth=max_depth,
                include=include,
                exclude=exclude,
            ),
            meta={"root": root},
        )

    @path_group.command("search")
    @root_option
    @traversal_options
    @click.option(
        "--mode",
        type=click.Choice(["exact", "contains", "fuzzy"], case_sensitive=False),
        default="contains",
        show_default=True,
        help="Path name search mode.",
    )
    @click.option(
        "--kind",
        type=click.Choice(["all", "directory"], case_sensitive=False),
        default="all",
        show_default=True,
        help="Path entry kind to scan.",
    )
    @click.option(
        "--limit",
        type=int,
        default=50,
        show_default=True,
        help="Maximum number of matches.",
    )
    @click.argument("query")
    @click.argument("start", default=".")
    @pass_runtime
    def search_command(
        runtime,
        root,
        include,
        exclude,
        max_depth,
        recursive,
        mode,
        kind,
        limit,
        query,
        start,
    ) -> None:
        runtime.executor.execute(
            "path.search",
            [start],
            lambda: runtime.facade.search.search_names(
                root,
                query=query,
                mode=mode,
                start=start,
                kind=kind,
                recursive=recursive,
                max_depth=max_depth,
                include=include,
                exclude=exclude,
                limit=limit,
            ),
            meta={"root": root},
        )

    return path_group

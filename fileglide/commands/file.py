"CLI commands for file lifecycle operations and file search."

from __future__ import annotations

import click

from fileglide.commands.common import (
    destination_root_option,
    destructive_options,
    pass_runtime,
    root_option,
    traversal_options,
)


def create_file_group() -> click.Group:
    """Create the file command group."""

    @click.group("file")
    def file_group() -> None:
        """Manage files inside a scoped root."""

    @file_group.command("create")
    @root_option
    @click.option(
        "--parents/--no-parents",
        default=False,
        help="Create missing parent directories.",
    )
    @click.option(
        "--exist-ok",
        is_flag=True,
        default=False,
        help="Allow the file to exist already.",
    )
    @click.argument("target")
    @pass_runtime
    def create_command(runtime, root, parents, exist_ok, target) -> None:
        runtime.executor.execute(
            "file.create",
            [target],
            lambda: runtime.facade.filesystem.create_file(
                root, target, parents=parents, exist_ok=exist_ok
            ),
            meta={"root": root},
        )

    @file_group.command("delete")
    @root_option
    @destructive_options
    @click.option(
        "--missing-ok",
        is_flag=True,
        default=False,
        help="Allow deleting a missing file.",
    )
    @click.argument("target")
    @pass_runtime
    def delete_command(runtime, root, dry_run, confirm, missing_ok, target) -> None:
        runtime.executor.execute(
            "file.delete",
            [target],
            lambda: runtime.facade.filesystem.delete_file(
                root,
                target,
                dry_run=dry_run,
                confirm=confirm,
                missing_ok=missing_ok,
            ),
            meta={"root": root, "dry_run": dry_run},
        )

    @file_group.command("move")
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
            "file.move",
            [source, destination],
            lambda: runtime.facade.filesystem.move_file(
                root,
                source,
                destination,
                destination_root=to_root,
                dry_run=dry_run,
                confirm=confirm,
            ),
            meta={"root": root, "to_root": to_root, "dry_run": dry_run},
        )

    @file_group.command("exists")
    @root_option
    @click.argument("target")
    @pass_runtime
    def exists_command(runtime, root, target) -> None:
        runtime.executor.execute(
            "file.exists",
            [target],
            lambda: runtime.facade.filesystem.exists(root, target),
            meta={"root": root},
        )

    @file_group.command("list")
    @root_option
    @traversal_options
    @click.argument("start", default=".")
    @pass_runtime
    def list_command(
        runtime, root, include, exclude, max_depth, recursive, start
    ) -> None:
        runtime.executor.execute(
            "file.list",
            [start],
            lambda: runtime.facade.traversal.list_entries(
                root,
                start=start,
                kind="file",
                recursive=recursive,
                max_depth=max_depth,
                include=include,
                exclude=exclude,
            ),
            meta={"root": root},
        )

    @file_group.command("search")
    @root_option
    @traversal_options
    @click.option(
        "--mode",
        type=click.Choice(["exact", "contains", "fuzzy"], case_sensitive=False),
        default="contains",
        show_default=True,
        help="File name search mode.",
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
        runtime, root, include, exclude, max_depth, recursive, mode, limit, query, start
    ) -> None:
        runtime.executor.execute(
            "file.search",
            [start],
            lambda: runtime.facade.search.search_names(
                root,
                query=query,
                mode=mode,
                start=start,
                kind="file",
                recursive=recursive,
                max_depth=max_depth,
                include=include,
                exclude=exclude,
                limit=limit,
            ),
            meta={"root": root},
        )

    return file_group

"""Commands for traversing mixed filesystem trees."""

from __future__ import annotations

import click

from fileglide.commands.common import pass_runtime, root_option, traversal_options


def create_tree_group() -> click.Group:
    """Create the tree command group."""

    @click.group("tree")
    def tree_group() -> None:
        """Traverse mixed file and directory trees."""

    @tree_group.command("list")
    @root_option
    @traversal_options
    @click.option(
        "--kind",
        type=click.Choice(["all", "file", "directory"], case_sensitive=False),
        default="all",
        show_default=True,
        help="Entry kind to include.",
    )
    @click.argument("start", default=".")
    @pass_runtime
    def list_command(
        runtime, root, include, exclude, max_depth, recursive, kind, start
    ) -> None:
        runtime.executor.execute(
            "tree.list",
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

    return tree_group

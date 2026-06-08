"""Commands for size, binary, and metadata inspection."""

from __future__ import annotations

import click

from fileglide.commands.common import pass_runtime, root_option


def create_inspect_group() -> click.Group:
    """Create the inspect command group."""

    @click.group("inspect")
    def inspect_group() -> None:
        """Inspect sizes, bytes, and binary-safe metadata."""

    @inspect_group.command("size")
    @root_option
    @click.argument("target")
    @pass_runtime
    def size_command(runtime, root, target) -> None:
        runtime.executor.execute(
            "inspect.size",
            [target],
            lambda: runtime.facade.sizing.stat_size(root, target),
            meta={"root": root},
        )

    @inspect_group.command("bytes")
    @root_option
    @click.option(
        "--offset",
        type=int,
        default=0,
        show_default=True,
        help="Byte offset to start reading.",
    )
    @click.option(
        "--length", type=int, default=None, help="Optional byte count to read."
    )
    @click.argument("target")
    @pass_runtime
    def bytes_command(runtime, root, offset, length, target) -> None:
        runtime.executor.execute(
            "inspect.bytes",
            [target],
            lambda: runtime.facade.binary.read_bytes(
                root, target, offset=offset, length=length
            ),
            meta={"root": root},
        )

    return inspect_group

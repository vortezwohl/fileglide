"""Commands for text reading, editing, searching, and binary workflows."""

from __future__ import annotations

import click

from fileglide.commands.common import pass_runtime, root_option, traversal_options


def create_text_group() -> click.Group:
    """Create the text command group."""

    @click.group("text")
    def text_group() -> None:
        """Operate on text and binary content."""

    @text_group.command("read")
    @root_option
    @click.option("--encoding", default=None, help="Force a specific text encoding.")
    @click.option("--start-line", type=int, default=None, help="First line to read.")
    @click.option("--end-line", type=int, default=None, help="Last line to read.")
    @click.argument("target")
    @pass_runtime
    def read_command(runtime, root, encoding, start_line, end_line, target) -> None:
        runtime.executor.execute(
            "text.read",
            [target],
            lambda: runtime.facade.text.read_text(
                root,
                target,
                encoding=encoding,
                start_line=start_line,
                end_line=end_line,
            ),
            meta={"root": root},
        )

    @text_group.command("write")
    @root_option
    @click.option(
        "--mode",
        type=click.Choice(["overwrite", "append", "insert"], case_sensitive=False),
        default="overwrite",
        show_default=True,
        help="Text write mode.",
    )
    @click.option("--encoding", default=None, help="Force a specific text encoding.")
    @click.option(
        "--position", type=int, default=None, help="Insert position for insert mode."
    )
    @click.option("--content", required=True, help="Text content to write.")
    @click.argument("target")
    @pass_runtime
    def write_command(runtime, root, mode, encoding, position, content, target) -> None:
        runtime.executor.execute(
            "text.write",
            [target],
            lambda: runtime.facade.text.write_text(
                root,
                target,
                content=content,
                mode=mode,
                encoding=encoding,
                position=position,
            ),
            meta={"root": root},
        )

    @text_group.command("replace-lines")
    @root_option
    @click.option("--encoding", default=None, help="Force a specific text encoding.")
    @click.option(
        "--start-line", type=int, required=True, help="First line to replace."
    )
    @click.option("--end-line", type=int, required=True, help="Last line to replace.")
    @click.option("--content", required=True, help="Replacement text.")
    @click.argument("target")
    @pass_runtime
    def replace_lines_command(
        runtime, root, encoding, start_line, end_line, content, target
    ) -> None:
        runtime.executor.execute(
            "text.replace-lines",
            [target],
            lambda: runtime.facade.text.replace_lines(
                root,
                target,
                start_line=start_line,
                end_line=end_line,
                content=content,
                encoding=encoding,
            ),
            meta={"root": root},
        )

    @text_group.command("insert-anchor")
    @root_option
    @click.option("--encoding", default=None, help="Force a specific text encoding.")
    @click.option(
        "--before/--after", default=False, help="Insert before or after the anchor."
    )
    @click.option("--anchor", required=True, help="Unique anchor string.")
    @click.option("--content", required=True, help="Text to insert.")
    @click.argument("target")
    @pass_runtime
    def insert_anchor_command(
        runtime, root, encoding, before, anchor, content, target
    ) -> None:
        runtime.executor.execute(
            "text.insert-anchor",
            [target],
            lambda: runtime.facade.text.insert_by_anchor(
                root,
                target,
                anchor=anchor,
                content=content,
                before=before,
                encoding=encoding,
            ),
            meta={"root": root},
        )

    @text_group.command("grep")
    @root_option
    @traversal_options
    @click.option("--encoding", default=None, help="Force a specific text encoding.")
    @click.argument("pattern")
    @click.argument("start", default=".")
    @pass_runtime
    def grep_command(
        runtime, root, include, exclude, max_depth, recursive, encoding, pattern, start
    ) -> None:
        runtime.executor.execute(
            "text.grep",
            [start],
            lambda: runtime.facade.search.regex_search(
                root,
                pattern=pattern,
                start=start,
                recursive=recursive,
                max_depth=max_depth,
                include=include,
                exclude=exclude,
                encoding=encoding,
            ),
            meta={"root": root},
        )

    @text_group.command("binary-write")
    @root_option
    @click.option(
        "--mode",
        type=click.Choice(["overwrite", "append", "insert"], case_sensitive=False),
        default="overwrite",
        show_default=True,
        help="Binary write mode.",
    )
    @click.option(
        "--offset", type=int, default=None, help="Insert offset for binary insert mode."
    )
    @click.option("--data-hex", required=True, help="Hex-encoded binary data.")
    @click.argument("target")
    @pass_runtime
    def binary_write_command(runtime, root, mode, offset, data_hex, target) -> None:
        runtime.executor.execute(
            "text.binary-write",
            [target],
            lambda: runtime.facade.binary.write_bytes(
                root,
                target,
                data=bytes.fromhex(data_hex),
                mode=mode,
                offset=offset,
            ),
            meta={"root": root},
        )

    @text_group.command("binary-copy")
    @root_option
    @click.argument("source")
    @click.argument("destination")
    @pass_runtime
    def binary_copy_command(runtime, root, source, destination) -> None:
        runtime.executor.execute(
            "text.binary-copy",
            [source, destination],
            lambda: runtime.facade.binary.copy_binary(root, source, destination),
            meta={"root": root},
        )

    return text_group

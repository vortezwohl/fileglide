"""Commands for text reading, editing, searching, and binary workflows."""

from __future__ import annotations

import click

from fileglide.commands.common import (
    binary_content_options,
    pass_runtime,
    resolve_binary_content_source,
    resolve_text_content_source,
    root_option,
    text_content_options,
    traversal_options,
)


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
    @text_content_options
    @click.argument("target")
    @pass_runtime
    def write_command(
        runtime,
        root,
        mode,
        encoding,
        position,
        content,
        content_file,
        content_stdin,
        target,
    ) -> None:
        runtime.executor.execute(
            "text.write",
            [target],
            lambda: _handle_text_write(
                runtime,
                root=root,
                target=target,
                mode=mode,
                encoding=encoding,
                position=position,
                content=content,
                content_file=content_file,
                content_stdin=content_stdin,
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
    @text_content_options
    @click.argument("target")
    @pass_runtime
    def replace_lines_command(
        runtime,
        root,
        encoding,
        start_line,
        end_line,
        content,
        content_file,
        content_stdin,
        target,
    ) -> None:
        runtime.executor.execute(
            "text.replace-lines",
            [target],
            lambda: _handle_replace_lines(
                runtime,
                root=root,
                target=target,
                encoding=encoding,
                start_line=start_line,
                end_line=end_line,
                content=content,
                content_file=content_file,
                content_stdin=content_stdin,
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
    @text_content_options
    @click.argument("target")
    @pass_runtime
    def insert_anchor_command(
        runtime,
        root,
        encoding,
        before,
        anchor,
        content,
        content_file,
        content_stdin,
        target,
    ) -> None:
        runtime.executor.execute(
            "text.insert-anchor",
            [target],
            lambda: _handle_insert_anchor(
                runtime,
                root=root,
                target=target,
                encoding=encoding,
                before=before,
                anchor=anchor,
                content=content,
                content_file=content_file,
                content_stdin=content_stdin,
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
    @binary_content_options
    @click.argument("target")
    @pass_runtime
    def binary_write_command(
        runtime,
        root,
        mode,
        offset,
        data_hex,
        data_file,
        data_stdin,
        target,
    ) -> None:
        runtime.executor.execute(
            "text.binary-write",
            [target],
            lambda: _handle_binary_write(
                runtime,
                root=root,
                target=target,
                mode=mode,
                offset=offset,
                data_hex=data_hex,
                data_file=data_file,
                data_stdin=data_stdin,
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


def _handle_text_write(
    runtime,
    *,
    root,
    target,
    mode,
    encoding,
    position,
    content,
    content_file,
    content_stdin,
):
    """Resolve payload input and dispatch the text write service."""

    resolved_content, content_source = resolve_text_content_source(
        runtime,
        content=content,
        content_file=content_file,
        content_stdin=content_stdin,
    )
    return runtime.facade.text.write_text(
        root,
        target,
        content=resolved_content,
        content_source=content_source,
        mode=mode,
        encoding=encoding,
        position=position,
    )


def _handle_replace_lines(
    runtime,
    *,
    root,
    target,
    encoding,
    start_line,
    end_line,
    content,
    content_file,
    content_stdin,
):
    """Resolve payload input and dispatch the line replacement service."""

    resolved_content, content_source = resolve_text_content_source(
        runtime,
        content=content,
        content_file=content_file,
        content_stdin=content_stdin,
    )
    return runtime.facade.text.replace_lines(
        root,
        target,
        start_line=start_line,
        end_line=end_line,
        content=resolved_content,
        content_source=content_source,
        encoding=encoding,
    )


def _handle_insert_anchor(
    runtime,
    *,
    root,
    target,
    encoding,
    before,
    anchor,
    content,
    content_file,
    content_stdin,
):
    """Resolve payload input and dispatch the anchor insertion service."""

    resolved_content, content_source = resolve_text_content_source(
        runtime,
        content=content,
        content_file=content_file,
        content_stdin=content_stdin,
    )
    return runtime.facade.text.insert_by_anchor(
        root,
        target,
        anchor=anchor,
        content=resolved_content,
        content_source=content_source,
        before=before,
        encoding=encoding,
    )


def _handle_binary_write(
    runtime,
    *,
    root,
    target,
    mode,
    offset,
    data_hex,
    data_file,
    data_stdin,
):
    """Resolve payload input and dispatch the binary write service."""

    payload, data_source = resolve_binary_content_source(
        data_hex=data_hex,
        data_file=data_file,
        data_stdin=data_stdin,
    )
    return runtime.facade.binary.write_bytes(
        root,
        target,
        data=payload,
        data_source=data_source,
        mode=mode,
        offset=offset,
    )

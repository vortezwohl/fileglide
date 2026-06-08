"""Root click command and top-level application options."""

from __future__ import annotations

import click

from fileglide import __version__
from fileglide.commands.batch import create_batch_group
from fileglide.commands.file import create_file_group
from fileglide.commands.inspect import create_inspect_group
from fileglide.commands.path import create_path_group
from fileglide.commands.text import create_text_group
from fileglide.commands.tree import create_tree_group
from fileglide.runtime import build_runtime


def create_root_command() -> click.Command:
    """Create the root click command tree."""

    @click.group(context_settings={"help_option_names": ["-h", "--help"]})
    @click.option(
        "--format",
        "output_format",
        type=click.Choice(["json", "text"], case_sensitive=False),
        default="json",
        show_default=True,
        help="Output format for command responses.",
    )
    @click.option(
        "--pretty/--compact",
        default=True,
        show_default=True,
        help="Pretty-print JSON output or emit compact JSON.",
    )
    @click.version_option(__version__, prog_name="fileglide")
    @click.pass_context
    def root(ctx: click.Context, output_format: str, pretty: bool) -> None:
        """Agent-oriented filesystem CLI with JSON as the default contract."""

        ctx.obj = build_runtime(output_format=output_format, pretty=pretty)

    root.add_command(create_file_group())
    root.add_command(create_path_group())
    root.add_command(create_tree_group())
    root.add_command(create_text_group())
    root.add_command(create_inspect_group())
    root.add_command(create_batch_group())
    return root

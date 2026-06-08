"""Application assembly entrypoint for the fileglide CLI."""

from fileglide.commands import create_root_command


def create_cli():
    """Create and return the root click command."""
    return create_root_command()

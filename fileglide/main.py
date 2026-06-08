"""Interpreter-facing entrypoint for the fileglide CLI."""

from __future__ import annotations

from fileglide.app import create_cli


def main() -> None:
    """Launch the click application."""
    create_cli()()


if __name__ == "__main__":
    main()

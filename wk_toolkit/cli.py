"""Main CLI entry point for wk-toolkit."""

from __future__ import annotations

import click

from wk_toolkit import __version__


@click.group()
@click.version_option(version=__version__, prog_name="wk-toolkit")
def cli() -> None:
    """wk-toolkit — a comprehensive toolkit for WebKit development."""


def _register_commands() -> None:
    """Import and register all command groups lazily."""
    from wk_toolkit.commands.analyze import analyze  # noqa: F811
    from wk_toolkit.commands.pr import pr
    from wk_toolkit.commands.branch import branch
    from wk_toolkit.commands.test import test
    from wk_toolkit.commands.bug import bug
    from wk_toolkit.commands.status import status

    cli.add_command(analyze)
    cli.add_command(pr)
    cli.add_command(branch)
    cli.add_command(test)
    cli.add_command(bug)
    cli.add_command(status)


_register_commands()

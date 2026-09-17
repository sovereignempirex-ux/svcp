"""
SCVP CLI
==========
Entry point registered as the `scvp` console script (see pyproject.toml).

Only `scvp init`, `scvp model`, and `scvp --version` are fully
implemented in this phase (Phase 0/1 -- Architecture + Core).
`scvp agent`, `scvp tool`, `scvp plugin`, `scvp search`, `scvp serve`,
`scvp test` are intentionally stubs that say so -- the command
surface is stable and scriptable from day one, but each stub is
filled in during its own phase (Agent Runtime, Tool System, Plugins,
Search, API, Testing) rather than faked now.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import click

from scvp.version import __version__

TEMPLATES_DIR = Path(__file__).parent / "templates"


@click.group()
@click.version_option(__version__, prog_name="scvp")
def cli() -> None:
    """SCVP — Scalable Cognitive Virtual Platform."""


@cli.command()
@click.argument("project_name")
@click.option(
    "--template",
    default="minimal",
    show_default=True,
    help="Which starter template to scaffold.",
)
def init(project_name: str, template: str) -> None:
    """Scaffold a new SCVP project in ./PROJECT_NAME."""
    src = TEMPLATES_DIR / template
    if not src.is_dir():
        available = ", ".join(sorted(p.name for p in TEMPLATES_DIR.iterdir() if p.is_dir()))
        click.echo(f"Unknown template '{template}'. Available: {available}", err=True)
        sys.exit(1)

    dest = Path.cwd() / project_name
    if dest.exists():
        click.echo(f"Directory '{dest}' already exists.", err=True)
        sys.exit(1)

    shutil.copytree(src, dest)
    click.echo(f"Created SCVP project at ./{project_name}")
    click.echo(f"Next steps:\n  cd {project_name}\n  pip install scvp\n  python main.py")


@cli.group()
def agent() -> None:
    """Manage agents. (Coming in Phase 3 — Agent Runtime.)"""


@agent.command("list")
def agent_list() -> None:
    click.echo("No agents yet -- Agent Runtime ships in Phase 3.")


@cli.group()
def tool() -> None:
    """Manage tools. (Coming in Phase 4 — Tool System.)"""


@tool.command("list")
def tool_list() -> None:
    click.echo("No tools yet -- Tool System ships in Phase 4.")


@cli.group()
def plugin() -> None:
    """Manage plugins. (Coming in Phase 9 — Plugins.)"""


@plugin.command("list")
def plugin_list() -> None:
    click.echo("No plugins yet -- Plugin System ships in Phase 9.")


@cli.command()
def model() -> None:
    """List registered model providers."""
    from scvp.models import model_registry  # local import keeps CLI startup cheap

    names = model_registry.list()
    if not names:
        click.echo("No model providers registered.")
        return
    click.echo("Registered model providers:")
    for n in names:
        click.echo(f"  - {n}")


@cli.command()
def search() -> None:
    """Manage search providers. (Coming in Phase 6 — Search.)"""
    click.echo("scvp search is not implemented yet -- Search System ships in Phase 6.")


@cli.command()
def serve() -> None:
    """Start the SCVP API server. (Coming in Phase 8 — API.)"""
    click.echo("scvp serve is not implemented yet -- API server ships in Phase 8.")


@cli.command()
def test() -> None:
    """Run the SCVP test suite for the current project. (Coming in Phase 12.)"""
    click.echo("scvp test is not implemented yet -- ships in Phase 12.")


if __name__ == "__main__":
    cli()

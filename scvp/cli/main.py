"""
SCVP CLI
==========
Entry point registered as the `scvp` console script (see pyproject.toml).

The command surface is backed by the runtime, provider registries, API,
plugin manager, and test runner implemented in the project.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

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
    """Run and inspect agents."""


@agent.command("list")
def agent_list() -> None:
    click.echo("Agents are configured by applications and exposed through the SDK/API.")


@agent.command("run")
@click.argument("goal")
@click.option("--provider", default="mock", show_default=True)
def agent_run(goal: str, provider: str) -> None:
    """Run a single agent goal with a registered model provider."""
    from scvp import Agent, SCVPModel

    result = Agent(model=SCVPModel(provider)).run(goal)
    click.echo(result.content)


@cli.group()
def tool() -> None:
    """Manage registered agent tools."""


@tool.command("list")
def tool_list() -> None:
    from scvp.tools import tool_registry

    names = tool_registry.list()
    click.echo("\n".join(names) if names else "No tools registered.")


@cli.group()
def plugin() -> None:
    """Discover and inspect installed plugins."""


@plugin.command("list")
def plugin_list() -> None:
    from scvp.plugins import PluginManager

    plugins = PluginManager().discover()
    if not plugins:
        click.echo("No plugins installed.")
        return
    for name, info in sorted(plugins.items()):
        click.echo(f"{name}\t{info.version}\t{info.description}")


@cli.group()
def model() -> None:
    """Manage model providers."""


@model.command("list")
def model_list() -> None:
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
    """Manage search providers."""
    from scvp.search import search_registry

    names = search_registry.list()
    click.echo("\n".join(names) if names else "No search providers registered.")


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8765, show_default=True, type=int)
def serve(host: str, port: int) -> None:
    """Start the SCVP FastAPI server."""
    try:
        import uvicorn
    except ImportError as exc:
        raise click.ClickException("Install API support with: pip install 'scvp[api]'") from exc
    uvicorn.run("scvp.api:create_app", factory=True, host=host, port=port)


@cli.command()
@click.option("-k", "keyword", default=None, help="Only run tests matching keyword.")
def test(keyword: Optional[str]) -> None:
    """Run the SCVP test suite for the current project."""
    command = [sys.executable, "-m", "pytest", "-q"]
    if keyword:
        command.extend(["-k", keyword])
    result = subprocess.run(command, check=False)
    if result.returncode:
        raise click.exceptions.Exit(result.returncode)


@cli.command("config")
@click.option("--key", default=None, help="Show one dotted configuration key.")
def config_show(key: Optional[str]) -> None:
    """Show effective non-secret configuration."""
    from scvp import load_config

    config = load_config()
    if key:
        value = config.get(key)
        click.echo(value if value is not None else "")
    else:
        click.echo(config.as_dict())


if __name__ == "__main__":
    cli()

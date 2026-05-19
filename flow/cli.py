import os
import re
import subprocess
import tempfile
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from .runner import run_runbook
from .store import (
    FLOW_DIR,
    delete,
    exists,
    load_all,
    load_one,
    parse_runbook,
    runbook_template,
    save,
)
from .tui import FlowTUI

app = typer.Typer(
    help="flow — interactive runbook runner",
    no_args_is_help=False,
    add_completion=False,
)
console = Console()


def _collect_vars(runbook) -> dict[str, str]:
    variables = runbook.all_vars()
    if not variables:
        return {}
    console.print()
    values = {}
    for v in variables:
        values[v] = typer.prompt(f"  {v}")
    return values


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context) -> None:
    """Open interactive fuzzy picker (default when no subcommand given)."""
    if ctx.invoked_subcommand is None:
        _interactive()


def _interactive() -> None:
    runbooks = load_all()
    if not runbooks:
        console.print(
            "[yellow]No runbooks yet.[/yellow] Create one with: [bold]flow new <name>[/bold]"
        )
        raise typer.Exit()

    runbook = FlowTUI().run()
    if not runbook:
        raise typer.Exit()

    values = _collect_vars(runbook)
    run_runbook(runbook, values)


@app.command("run")
def cmd_run(
    name: Annotated[str, typer.Argument(help="Runbook name")],
) -> None:
    """Run a runbook by name."""
    runbook = load_one(name)
    if not runbook:
        console.print(f"[red]No runbook named '{name}'.[/red]")
        raise typer.Exit(1)
    values = _collect_vars(runbook)
    run_runbook(runbook, values)


@app.command("ls")
def cmd_list(
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Filter by tag")] = None,
) -> None:
    """List all runbooks."""
    runbooks = load_all()
    if tag:
        runbooks = [rb for rb in runbooks if tag in rb.tags]

    if not runbooks:
        console.print("[dim]No runbooks found.[/dim]")
        return

    table = Table(
        show_header=True, header_style="bold", box=None, pad_edge=False, show_edge=False
    )
    table.add_column("Name", style="cyan", min_width=22, no_wrap=True)
    table.add_column("Description", ratio=3)
    table.add_column("Steps", justify="right", style="dim", min_width=5)
    table.add_column("Tags", style="green", min_width=12)

    for rb in runbooks:
        table.add_row(rb.name, rb.desc or "", str(len(rb.steps)), ", ".join(rb.tags))

    console.print(table)


@app.command("new")
def cmd_new(
    name: Annotated[str, typer.Argument(help="Runbook name")],
) -> None:
    """Create a new runbook and open it in $EDITOR."""
    if exists(name):
        console.print(f"[red]Runbook '{name}' already exists. Use 'flow edit {name}'.[/red]")
        raise typer.Exit(1)

    editor = os.environ.get("EDITOR", "nano")
    content = runbook_template(name)

    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write(content)
        tmp = f.name

    try:
        subprocess.run([editor, tmp], check=True)
        import yaml
        data = yaml.safe_load(open(tmp).read())
        runbook = parse_runbook(data)
        runbook.name = name
        save(runbook)
        console.print(
            f"[green]Saved[/green] [bold cyan]{name}[/bold cyan]"
            f"  [dim]({len(runbook.steps)} steps)[/dim]"
        )
    except Exception as e:
        console.print(f"[red]Could not save runbook: {e}[/red]")
        raise typer.Exit(1)
    finally:
        os.unlink(tmp)


@app.command("edit")
def cmd_edit(
    name: Annotated[str, typer.Argument(help="Runbook name")],
) -> None:
    """Open a runbook in $EDITOR."""
    path = FLOW_DIR / f"{name}.yaml"
    if not path.exists():
        console.print(f"[red]No runbook named '{name}'.[/red]")
        raise typer.Exit(1)
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, str(path)])
    console.print(f"[green]Saved[/green] [cyan]{name}[/cyan]")


@app.command("show")
def cmd_show(
    name: Annotated[str, typer.Argument(help="Runbook name")],
) -> None:
    """Show full details of a runbook."""
    runbook = load_one(name)
    if not runbook:
        console.print(f"[red]No runbook named '{name}'.[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]{runbook.name}[/bold cyan]  [dim]{runbook.desc}[/dim]")
    if runbook.tags:
        console.print(f"[green]{', '.join(runbook.tags)}[/green]")

    vars_ = runbook.all_vars()
    if vars_:
        console.print(f"\n[dim]Variables:[/dim] {', '.join('{{' + v + '}}' for v in vars_)}")

    console.print()
    for i, step in enumerate(runbook.steps, 1):
        console.print(f"  [{i}]  [bold]{step.name}[/bold]")
        console.print(f"       [dim]$ {step.cmd}[/dim]")
        if step.desc:
            console.print(f"       [dim]{step.desc}[/dim]")
        if step.confirm:
            console.print(f"       [yellow]requires confirmation[/yellow]")
    console.print()


@app.command("rm")
def cmd_remove(
    name: Annotated[str, typer.Argument(help="Runbook name")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a runbook."""
    if not exists(name):
        console.print(f"[red]No runbook named '{name}'.[/red]")
        raise typer.Exit(1)
    if not yes:
        typer.confirm(f"Delete '{name}'?", abort=True)
    delete(name)
    console.print(f"[green]Deleted[/green] [cyan]{name}[/cyan].")

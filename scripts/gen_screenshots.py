#!/usr/bin/env python3
"""Generate SVG screenshots for flow's README."""

import asyncio
import sys
from pathlib import Path

# Run from the flow/ project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.rule import Rule

OUT = Path(__file__).parent.parent / "screenshots"
OUT.mkdir(exist_ok=True)

WIDTH = 82


def console() -> Console:
    return Console(record=True, force_terminal=True, width=WIDTH)


# ── ls ────────────────────────────────────────────────────────────────────────

def make_ls():
    c = console()

    table = Table(
        show_header=True,
        header_style="bold",
        box=None,
        pad_edge=False,
        show_edge=False,
    )
    table.add_column("Name", style="cyan", min_width=18, no_wrap=True)
    table.add_column("Description", ratio=3)
    table.add_column("Steps", justify="right", style="dim", min_width=5)
    table.add_column("Tags", style="green", min_width=14)

    rows = [
        ("deploy-prod", "Deploy a service to production",    "5", "deploy, k8s"),
        ("setup-dev",   "Bootstrap local dev environment",   "4", "setup"),
        ("db-migrate",  "Run database migrations safely",    "3", "database"),
        ("rollback",    "Rollback last deployment",          "3", "deploy, k8s"),
    ]
    for row in rows:
        table.add_row(*row)

    c.print(table)
    c.save_svg(str(OUT / "ls.svg"), title="flow ls")
    print("✓  ls.svg")


# ── run (mid-execution) ───────────────────────────────────────────────────────

def make_run():
    c = console()

    c.print()
    c.rule("[bold]deploy-prod[/bold]", style="dim")
    c.print("  [dim]Deploy a service to production[/dim]")
    c.print()
    c.print("  [dim]service[/dim]  →  [cyan]api-gateway[/cyan]")
    c.print("  [dim]version[/dim]  →  [cyan]1.4.2[/cyan]")
    c.print()

    # step 1 — done
    c.rule(style="dim")
    c.print("\n  [bold][1/5][/bold]  Run tests")
    c.print("  [dim]$ make test SERVICE=api-gateway[/dim]")
    c.print()
    c.print("  [bold]r[/bold] run   [bold]s[/bold] skip   [bold]q[/bold] quit  r")
    c.print()
    c.print("  All tests passed (42 cases).")
    c.print()
    c.print("  [green]✓[/green]  [dim]2.3s[/dim]")

    # step 2 — currently running
    c.rule(style="dim")
    c.print("\n  [bold][2/5][/bold]  Build image")
    c.print("  [dim]$ docker build -t api-gateway:1.4.2 .[/dim]")
    c.print()
    c.print("  [bold]r[/bold] run   [bold]s[/bold] skip   [bold]q[/bold] quit  r")
    c.print()
    c.print("  Step 1/4 : FROM python:3.12-slim")
    c.print("  Step 2/4 : COPY requirements.txt .")
    c.print("  Step 3/4 : RUN pip install -r requirements.txt")
    c.print()

    c.save_svg(str(OUT / "run.svg"), title="flow run deploy-prod")
    print("✓  run.svg")


# ── summary ───────────────────────────────────────────────────────────────────

def make_summary():
    c = console()

    c.print()
    c.rule("[bold]Summary[/bold]", style="dim")
    c.print()

    rows = [
        ("[green]✓[/green]", "Run tests",        "2.3s"),
        ("[green]✓[/green]", "Build image",       "12.1s"),
        ("[green]✓[/green]", "Push to registry",  "4.2s"),
        ("[red]✗[/red]",     "Deploy",            "0.3s"),
        ("[dim]–[/dim]",     "Watch rollout",     ""),
    ]
    for i, (icon, name, dur) in enumerate(rows, 1):
        dur_str = f"  [dim]{dur}[/dim]" if dur else ""
        c.print(f"  [{i}/5]  {name:<32} {icon}{dur_str}")

    c.print()
    c.print("  [green]3 passed[/green]  [red]1 failed[/red]  [dim]1 skipped[/dim]")
    c.print()

    c.save_svg(str(OUT / "summary.svg"), title="flow — summary")
    print("✓  summary.svg")


# ── picker (Textual TUI screenshot) ──────────────────────────────────────────

async def make_picker():
    from flow.tui import FlowTUI

    app = FlowTUI()
    async with app.run_test(size=(90, 24)) as pilot:
        await pilot.pause(0.3)
        app.save_screenshot(str(OUT / "picker.svg"))
    print("✓  picker.svg")


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    make_ls()
    make_run()
    make_summary()
    asyncio.run(make_picker())
    print(f"\nAll screenshots saved to {OUT}/")

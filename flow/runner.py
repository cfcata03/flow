import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from rich.console import Console

from .runbook import Runbook

console = Console()


class Status(Enum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    status: Status = Status.PENDING
    duration: float = 0.0
    exit_code: Optional[int] = None


_ICONS = {
    Status.DONE:    "[green]✓[/green]",
    Status.FAILED:  "[red]✗[/red]",
    Status.SKIPPED: "[dim]–[/dim]",
    Status.PENDING: "[dim]·[/dim]",
}


def _getch() -> str:
    if not sys.stdin.isatty():
        return sys.stdin.read(1)
    import termios, tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _prompt(options: str) -> str:
    console.print(f"\n  {options}  ", end="")
    key = _getch().lower()
    console.print(key)
    return key


def run_runbook(runbook: Runbook, values: dict[str, str]) -> list[StepResult]:
    total = len(runbook.steps)
    results: list[StepResult] = [StepResult() for _ in runbook.steps]

    console.print()
    console.rule(f"[bold]{runbook.name}[/bold]", style="dim")
    if runbook.desc:
        console.print(f"  [dim]{runbook.desc}[/dim]")

    if values:
        console.print()
        for k, v in values.items():
            console.print(f"  [dim]{k}[/dim]  →  [cyan]{v}[/cyan]")

    console.print()

    i = 0
    while i < total:
        step = runbook.steps[i]
        result = results[i]
        cmd = runbook.render_step_cmd(step.cmd, values)

        console.rule(style="dim")
        console.print(f"\n  [bold][{i + 1}/{total}][/bold]  {step.name}")
        if step.desc:
            console.print(f"  [dim]{step.desc}[/dim]")
        console.print(f"  [dim]$ {cmd}[/dim]")

        if step.confirm:
            console.print("\n  [yellow]This step requires explicit confirmation.[/yellow]")

        key = _prompt("[bold]r[/bold] run   [bold]s[/bold] skip   [bold]q[/bold] quit")

        if key == "q":
            for j in range(i, total):
                results[j].status = Status.SKIPPED
            break

        if key == "s":
            result.status = Status.SKIPPED
            i += 1
            continue

        # run
        console.print()
        start = time.time()
        proc = subprocess.run(cmd, shell=True)
        result.duration = time.time() - start
        result.exit_code = proc.returncode
        result.status = Status.DONE if proc.returncode == 0 else Status.FAILED

        icon = _ICONS[result.status]
        console.print(f"\n  {icon}  [dim]{result.duration:.1f}s[/dim]")

        if result.status == Status.FAILED:
            console.print(f"  [red]Step failed (exit {result.exit_code}).[/red]")
            key2 = _prompt("[bold]c[/bold] continue   [bold]r[/bold] retry   [bold]q[/bold] quit")
            if key2 == "q":
                for j in range(i + 1, total):
                    results[j].status = Status.SKIPPED
                i += 1
                break
            if key2 == "r":
                result.status = Status.PENDING
                result.duration = 0.0
                result.exit_code = None
                continue  # retry same step without incrementing i

        i += 1

    _print_summary(runbook, results)
    return results


def _print_summary(runbook: Runbook, results: list[StepResult]) -> None:
    total = len(runbook.steps)
    console.print()
    console.rule("[bold]Summary[/bold]", style="dim")
    console.print()

    for i, (step, result) in enumerate(zip(runbook.steps, results), 1):
        icon = _ICONS[result.status]
        dur = f"  [dim]{result.duration:.1f}s[/dim]" if result.duration else ""
        console.print(f"  [{i}/{total}]  {step.name:<32} {icon}{dur}")

    console.print()

    done    = sum(1 for r in results if r.status == Status.DONE)
    failed  = sum(1 for r in results if r.status == Status.FAILED)
    skipped = sum(1 for r in results if r.status == Status.SKIPPED)

    parts = []
    if done:    parts.append(f"[green]{done} passed[/green]")
    if failed:  parts.append(f"[red]{failed} failed[/red]")
    if skipped: parts.append(f"[dim]{skipped} skipped[/dim]")
    console.print("  " + "  ".join(parts))
    console.print()

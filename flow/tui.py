from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Input, Label, ListItem, ListView

from .runbook import Runbook
from .search import fuzzy_search
from .store import load_all


class RunbookItem(ListItem):
    def __init__(self, runbook: Runbook) -> None:
        super().__init__()
        self.runbook = runbook

    def compose(self) -> ComposeResult:
        tags = (
            f"  [dim green][{', '.join(self.runbook.tags)}][/dim green]"
            if self.runbook.tags
            else ""
        )
        steps_str = f"  [dim]{len(self.runbook.steps)} steps[/dim]"
        yield Label(f"[bold cyan]{self.runbook.name}[/bold cyan]{tags}{steps_str}")
        if self.runbook.desc:
            yield Label(f"  [dim]{self.runbook.desc}[/dim]")


class FlowTUI(App[Optional[Runbook]]):
    CSS = """
    Screen { background: $surface; }
    Input { margin: 1 2 0 2; border: tall $accent; }
    #subtitle { margin: 0 2 0 2; color: $text-muted; height: 1; }
    ListView { margin: 0 2 1 2; height: 1fr; border: round $panel; }
    RunbookItem { height: 2; padding: 0 1; }
    RunbookItem.--highlight { background: $accent 20%; }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "confirm", "Select"),
        Binding("up", "cursor_up", show=False),
        Binding("down", "cursor_down", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._all: list[Runbook] = load_all()

    def compose(self) -> ComposeResult:
        yield Input(placeholder="search runbooks...", id="search")
        yield Label("", id="subtitle")
        yield ListView(id="results")

    def on_mount(self) -> None:
        self._refresh(self._all)
        self.query_one(Input).focus()

    def _refresh(self, runbooks: list[Runbook]) -> None:
        lv = self.query_one("#results", ListView)
        lv.clear()
        for rb in runbooks:
            lv.append(RunbookItem(rb))
        self.query_one("#subtitle", Label).update(
            f"[dim]{len(runbooks)}/{len(self._all)} runbooks"
            "  •  ↑↓ navigate  Enter select  Esc cancel[/dim]"
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        self._refresh(fuzzy_search(self._all, event.value))

    def _current(self) -> Optional[Runbook]:
        lv = self.query_one("#results", ListView)
        if lv.highlighted_child and isinstance(lv.highlighted_child, RunbookItem):
            return lv.highlighted_child.runbook
        for item in lv.query(RunbookItem):
            return item.runbook
        return None

    def action_cancel(self) -> None:
        self.exit(None)

    def action_confirm(self) -> None:
        self.exit(self._current())

    def action_cursor_up(self) -> None:
        self.query_one("#results", ListView).action_cursor_up()

    def action_cursor_down(self) -> None:
        self.query_one("#results", ListView).action_cursor_down()

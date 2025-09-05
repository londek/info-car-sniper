from __future__ import annotations

from textual.widgets import Static, Label
from textual.containers import Horizontal
from textual.app import ComposeResult

class StatPanel(Static):
    DEFAULT_CSS = """
        .lbl {
            width: 30;
            height: 1;
        }
        
        .row {
            width: auto;
            height: auto;
        }

        .val {
            width: auto;
            height: 1;
        }
    """

    def __init__(self, title: str, body: str = "-", id: str | None = None) -> None:
        super().__init__(id=id)
        self.title = title
        self.init_text = body

    def compose(self) -> ComposeResult:
        self.value = Static(self.init_text, classes="val")

        yield Horizontal(
            Label(self.title, classes="lbl"),
            self.value,
            classes="row",
        )

    def update_value(self, text: str) -> None:
        self.value.update(text)

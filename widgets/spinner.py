from __future__ import annotations

from time import time
from typing import TYPE_CHECKING

from rich.text import Text

from textual import on
from textual.events import InputEvent, Mount
from textual.widget import Widget

if TYPE_CHECKING:
    from textual.app import RenderResult

class Spinner(Widget):
    DEFAULT_CSS = """
    Spinner {
        width: 1;
        height: 1;
        content-align: center middle;
        color: $primary;
        text-style: not reverse;
    }
    """

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        *,
        speed: float = 1.0,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._start_time: float = 0.0
        self._speed = max(0.1, float(speed))
        # Frames for a classic spinner animation
        self._frames = (
            "⠋",
            "⠙",
            "⠹",
            "⠸",
            "⠼",
            "⠴",
            "⠦",
            "⠧",
            "⠇",
            "⠏",
        )

    def _on_mount(self, _: Mount) -> None:
        self._start_time = time()
        # ~60 FPS
        self.auto_refresh = 1 / 16

    @on(InputEvent)
    def on_input(self, event: InputEvent) -> None:
        """Prevent all input events from bubbling while loading."""
        event.stop()
        event.prevent_default()

    def render(self) -> RenderResult:
        # Fallback when animations are disabled
        if self.app.animation_level == "none":
            return Text("Loading…")

        elapsed = time() - self._start_time

        # Pick current frame based on elapsed time and speed
        idx = int(elapsed * self._speed * len(self._frames)) % len(self._frames)
        ch = self._frames[idx]

        return Text(ch)

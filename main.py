from __future__ import annotations

from textual.app import App
from textual.binding import Binding
from config_manager import load_config
from screens.login_screen import LoginScreen
from app_state import AppState

class InfoCarApp(App):
    TITLE = "Info-Car Looker"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True, show=False),
    ]

    CSS = """
    App, Screen {
        padding: 0 !important;
        background: transparent;
        content-align: center middle;
        align: center middle;
        outline: none;
        border: none;
    }

    LoginScreen {
        background: transparent;
        align: center middle;
    }

    MainScreen {
        align: center middle;
        background: transparent;
    }
    """

    def on_mount(self) -> None:
        self.state = AppState()
        
        cfg = load_config()
        if cfg.username and cfg.password and cfg.capmonster_key:
            self.push_screen(LoginScreen(auto_login=True))
        else:
            self.push_screen(LoginScreen())

    def action_quit(self) -> None:
        self.exit()


if __name__ == "__main__":
    InfoCarApp().run(inline=True)


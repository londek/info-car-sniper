from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Center, Container
from textual.widgets import Button, Input, Label, Static
from textual.screen import Screen
from textual.binding import Binding

from datetime import datetime, timedelta
import re
import threading

from capmonster_provider import CapmonsterProvider
from infocar import InfoCarSession
from app_state import AppState
from config_manager import AppConfig, load_config, save_config

from widgets.spinner import Spinner
from screens.main_screen import MainScreen

class LoginScreen(Screen):
    BINDINGS = [
        Binding("enter", "login", "Login", priority=True, show=False),
        Binding("up", "focus_prev", show=False),
        Binding("down", "focus_next", show=False),
    ]

    CSS = """
    #ticker_container {
        height: auto;
        width: auto;
    }

    #ticker_text {
        padding-left: 1;
        text-style: bold;
        height: auto;
        width: auto;
    }

    #spinner {
        color: white;
        text-style: bold;
    }

    .row {
        width: 100%;
        height: auto;
    }

    .val {
        width: 100%;
        content-align: right middle;
        text-align: right;
    }

    .lbl {
        width: 22;
        color: gray;
    }

    .fld {
        padding: 0;
        margin: 0;
        height: 1;
        border: none;
        width: 100%;
    }

    .hidden {
        display: none;
    }

    #main_container {
        height: auto;
        width: 60;
        border: round gray;
        padding: 1 6 1 6;
    }

    #errors {
        text-align: center;
        color: red;
        height: auto;
    }
    """

    def __init__(self, auto_login: bool = False) -> None:
        super().__init__()
        self.auto_login = auto_login

    def compose(self) -> ComposeResult:
        cfg = load_config()

        # Smart defaults
        today = datetime.now().date()
        default_from = cfg.date_from or today.strftime("%Y-%m-%d")
        default_to = cfg.date_to or (today + timedelta(days=60)).strftime("%Y-%m-%d")
        default_h_from = cfg.hour_from or "07:00"
        default_h_to = cfg.hour_to or "20:00"

        main_container = Container(
            Static(),
            Center(Horizontal(
                Label("Username", classes="lbl"),
                Input(placeholder="email@example.com", id="username", value=cfg.username, classes="fld"),
                classes="row",
            )),
            Center(Horizontal(
                Label("Password", classes="lbl"),
                Input(placeholder="••••••••", password=True, id="password", value=cfg.password, classes="fld"),
                classes="row",
            )),
            Center(Horizontal(
                Label("Capmonster Key", classes="lbl"),
                Input(placeholder="xxxxxxxxxxxxxxxxxxxxxxxx", password=True, id="capmonster", value=cfg.capmonster_key, classes="fld"),
                classes="row",
            )),
            Static(),
            Center(Horizontal(
                Label("Date from", classes="lbl"),
                Input(placeholder="YYYY-MM-DD", id="date_from", value=default_from, classes="fld"),
                classes="row",
            )),
            Center(Horizontal(
                Label("Date to", classes="lbl"),
                Input(placeholder="YYYY-MM-DD", id="date_to", value=default_to, classes="fld"),
                classes="row",
            )),
            Static(),
            Center(Horizontal(
                Label("Hour from", classes="lbl"),
                Input(placeholder="HH:MM", id="hour_from", value=default_h_from, classes="fld"),
                classes="row",
            )),
            Center(Horizontal(
                Label("Hour to", classes="lbl"),
                Input(placeholder="HH:MM", id="hour_to", value=default_h_to, classes="fld"),
                classes="row",
            )),
            Center(
                Horizontal(
                    Spinner(id="spinner"),
                    Static(id="ticker_text"),
                    id="ticker_container",
                    classes="hidden"
                ),
            ),
            Center(Static(id="errors")),
            id="main_container",
        )

        main_container.border_title = "Info-Car Sniper - Login"
        main_container.border_subtitle = "Ctrl+c exit • ↑↓/tab navigate • Enter submit"

        yield main_container

    def action_focus_next(self) -> None:
            self.focus_next()

    def action_focus_prev(self) -> None:
            self.focus_previous()

    def on_mount(self) -> None:
        if self.auto_login:
            username: Input = self.query_one("#username")
            password: Input = self.query_one("#password")
            capmonster: Input = self.query_one("#capmonster")
            if username.value and password.value and capmonster.value:
                self.action_login()
        else:
            self.set_focus(self.query_one("#username"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login":
            self.action_login()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.action_login()

    def action_login(self) -> None:
        ticker_text: Static = self.query_one("#ticker_text")
        ticker_container: Horizontal = self.query_one("#ticker_container")

        errors: Static = self.query_one("#errors")
        username: Input = self.query_one("#username")
        password: Input = self.query_one("#password")
        capmonster: Input = self.query_one("#capmonster")
        date_from_in: Input = self.query_one("#date_from")
        date_to_in: Input = self.query_one("#date_to")
        hour_from_in: Input = self.query_one("#hour_from")
        hour_to_in: Input = self.query_one("#hour_to")

        try:
            errors.update("")
            errors.add_class("hidden")
        except Exception:
            pass

        email = username.value.strip()
        pwd = password.value.strip()
        cap = capmonster.value.strip()
        date_from = date_from_in.value.strip()
        date_to = date_to_in.value.strip()
        hour_from = hour_from_in.value.strip()
        hour_to = hour_to_in.value.strip()

        def valid_email(addr: str) -> bool:
            return re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", addr) is not None

        def valid_date(s: str) -> bool:
            try:
                datetime.strptime(s, "%Y-%m-%d")
                return True
            except Exception:
                return False

        def valid_time(s: str) -> bool:
            return re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", s) is not None

        if not email:
            errors.remove_class("hidden")
            errors.update("Email is required")
            self.set_focus(username)
            return
        if not valid_email(email):
            errors.remove_class("hidden")
            errors.update("Invalid email format")
            self.set_focus(username)
            return
        if not pwd:
            errors.remove_class("hidden")
            errors.update("Password is required")
            self.set_focus(password)
            return
        if not cap:
            errors.remove_class("hidden")
            errors.update("Capmonster Key is required")
            self.set_focus(capmonster)
            return

        # Validate date/time ranges (smart checks)
        if not valid_date(date_from):
            errors.remove_class("hidden")
            errors.update("Date from must be YYYY-MM-DD")
            self.set_focus(date_from_in)
            return
        if not valid_date(date_to):
            errors.remove_class("hidden")
            errors.update("Date to must be YYYY-MM-DD")
            self.set_focus(date_to_in)
            return
        if not valid_time(hour_from):
            errors.remove_class("hidden")
            errors.update("Hour from must be HH:MM (24h)")
            self.set_focus(hour_from_in)
            return
        if not valid_time(hour_to):
            errors.remove_class("hidden")
            errors.update("Hour to must be HH:MM (24h)")
            self.set_focus(hour_to_in)
            return

        try:
            df_dt = datetime.strptime(date_from, "%Y-%m-%d")
            dt_dt = datetime.strptime(date_to, "%Y-%m-%d")
            hf = datetime.strptime(hour_from, "%H:%M")
            ht = datetime.strptime(hour_to, "%H:%M")
        except Exception:
            errors.remove_class("hidden")
            errors.update("Invalid date/time values")
            return

        if df_dt > dt_dt:
            errors.remove_class("hidden")
            errors.update("Date from must be before or equal to Date to")
            self.set_focus(date_from_in)
            return
        if hf >= ht:
            errors.remove_class("hidden")
            errors.update("Hour from must be earlier than Hour to")
            self.set_focus(hour_from_in)
            return

        if dt_dt < datetime.now() - timedelta(days=1):
            errors.remove_class("hidden")
            errors.update("Date range appears to be in the past")
            self.set_focus(date_to_in)
            return

        ticker_text.update("Checking Capmonster balance…")
        ticker_container.remove_class("hidden")

        def do_login():
            try:
                try:
                    provider = CapmonsterProvider(capmonster.value)
                    balance = provider.get_balance()
                except Exception as e:
                    raise e
            
                if balance <= 0:
                    raise Exception("CapMonster balance is 0. Please top up.")
                
                proxies = []

                try:
                    with open("proxies.txt", "r") as f:
                        proxies = f.read().splitlines()
                except:
                    pass

                self.app.call_from_thread(ticker_text.update, "Logging in to Info-Car…")

                # Reuse existing session if available; otherwise create new
                app_state: AppState = getattr(self.app, "state", AppState())
                if app_state.session is None:
                    app_state.session = InfoCarSession(capmonster.value, proxies=proxies)
                else:
                    # Update capmonster key/proxies if changed
                    app_state.session.capmonster = app_state.session.capmonster.__class__(api_key=capmonster.value)
                    app_state.session.proxies = proxies
                infocar_session = app_state.session
                infocar_session.login(username.value, password.value)

                self.app.call_from_thread(ticker_text.update, "Fetching reservations…")
                
                reservations = infocar_session.get_account_reservations()
                reservation = reservations[0]

                self.app.call_from_thread(ticker_text.update, "Verifying details…")

                if not infocar_session.is_reschedule_enabled_for_word(reservation['exam']['organizationUnitId']):
                    raise Exception("Rescheduling is not enabled for your driving test center.")

                cfg = AppConfig(
                    username=username.value,
                    password=password.value,
                    capmonster_key=capmonster.value,
                    date_from=date_from,
                    date_to=date_to,
                    hour_from=hour_from,
                    hour_to=hour_to,
                )
                save_config(cfg)
                # Persist in global state
                app_state.cfg = cfg
                app_state.reservation = reservation

                self.app.call_from_thread(self.app.switch_screen, MainScreen(session=infocar_session, cfg=cfg, reservation=reservation))
            except Exception as e:
                def handle_login_error():
                    ticker_text.text = ""
                    ticker_container.add_class("hidden")
                    errors.remove_class("hidden")
                    errors.update(str(e))

                self.app.call_from_thread(handle_login_error)
            finally:
                self.app.call_from_thread(ticker_container.add_class, "hidden")

        threading.Thread(target=do_login, daemon=True).start()

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Container, Center, Horizontal
from textual.widgets import Static
import playsound3

from datetime import datetime, timedelta
import time
import threading
import random

from infocar import AuthenticationError, InfoCarSession, PRACTICE_EXAM_TYPE
from config_manager import AppConfig
from widgets.spinner import Spinner

from widgets.stat_panel import StatPanel
from constants import FUNNY_TICKER_WAITING_TEXTS
from screens.reschedule_screen import RescheduleScreen
from app_state import AppState

class MainScreen(Screen):
    BINDINGS = [
        Binding("ctrl+l", "logout", "Logout", show=False, priority=True),
    ]

    CSS = """
        #main_container {
            background: transparent;
            align: center middle;
            content-align: center middle;
            border: round gray;
            padding: 2 6 1 6;
            width: 60;
            height: auto;
        }

        Center Static {
            width: auto;
            content-align: center middle;
            align: center middle;
        }

        #searching_for {
            text-style: bold;
            color: cyan;
        }

        #last_error {
            min-height: 1;
            max-height: 3;
            height: auto;
            text-align: center;
            color: red;
        }

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
    """

    def __init__(self, session: InfoCarSession, cfg: AppConfig, reservation) -> None:
        super().__init__()
        self.session = session
        self.cfg = cfg
        self.reservation = reservation

        self.ticker = None
        self.running = False
        self.poll_thread = None
        self._ticker_timer = None
        self.stats = None

    def compose(self) -> ComposeResult:
        reservation_date = time.strptime(self.reservation['exam']['practice']['date'], "%Y-%m-%dT%H:%M:%S")
        searching_for_text = self._compute_elapsed_text_safe()

        main_container = Container(
            Center(Static(f"Searching for {searching_for_text}", id="searching_for")),
            StatPanel("Turnstile usage", id="turnstile"),
            StatPanel("All checks", id="all_checks"),
            StatPanel("Earliest ever exam date", id="earliest_ever"),
            StatPanel("Current earliest exam date", id="current_earliest"),
            StatPanel("Last found exam date", id="last_found"),
            Static(),
            Center(Static(f"{time.strftime('%Y-%m-%d %H:%M', reservation_date)} at {self.reservation['exam']['organizationUnitName']}")),
            Center(Static(f"Searching dates: {self.cfg.date_from} → {self.cfg.date_to}")),
            Center(Static(f"Searching hours: {self.cfg.hour_from} → {self.cfg.hour_to}")),
            Static(),
            Center(
                Horizontal(
                    Spinner(id="spinner"),
                    Static("Finding best time…", id="ticker_text"),
                    id="ticker_container"
                ),
            ),
            Center(Static(id="last_error")),
            id="main_container",
        )

        main_container.border_title = "Info-Car Sniper"
        main_container.border_subtitle = "Ctrl+l logout • Ctrl+c exit"

        yield main_container

    def on_mount(self) -> None:
        self.last_error_panel = self.query_one("#last_error")
        # Attach shared state
        app_state: AppState = getattr(self.app, "state")
        self.stats = app_state.stats
        
        # If re-entered, prefer persisted cfg/reservation if available
        if getattr(app_state, "cfg", None) is not None:
            self.cfg = app_state.cfg  # type: ignore
        if getattr(app_state, "reservation", None) is not None:
            self.reservation = app_state.reservation

        try:
            if app_state.started_checking_at is None:
                app_state.started_checking_at = datetime.now()

            searching_for = self._compute_elapsed_text_safe()
            self.query_one("#searching_for", Static).update(f"Searching for {searching_for}")
        except Exception:
            pass

        self.running = True
        self.update_panels()

        self.poll_thread = threading.Thread(target=self.poll_loop, daemon=True)
        self.poll_thread.start()

        def _rotate_ticker_text_event() -> None:
            try:
                ticker_text_widget: Static = self.query_one("#ticker_text")
                ticker_text_widget.update(random.choice(FUNNY_TICKER_WAITING_TEXTS))
            except Exception:
                pass

        self._ticker_timer = self.set_interval(15.0, _rotate_ticker_text_event)
        # Also update elapsed banner every 10s
        self.set_interval(10.0, self._update_elapsed_banner)

    def on_unmount(self) -> None:
        if self._ticker_timer is not None:
            try:
                self._ticker_timer.stop()
            except Exception:
                pass

    def action_logout(self) -> None:
        self.running = False

        # Lazy import to avoid circular import at module load time
        from screens.login_screen import LoginScreen
        self.app.switch_screen(LoginScreen())

    def poll_loop(self):
        try:
            while self.running:
                try:
                    exams = []

                    for retry in range(5):
                        try:
                            exams = self.session.get_exams(
                                PRACTICE_EXAM_TYPE,
                                word_id=self.reservation['exam']['organizationUnitId'],
                            )
                            break
                        except AuthenticationError as e:
                            self.running = False
                            # Lazy import to avoid circular import at module load time
                            from screens.login_screen import LoginScreen
                            self.app.call_from_thread(self.app.switch_screen, LoginScreen(auto_login=True))
                            return
                        except Exception as e:
                            if retry == 4:
                                raise e
                            
                            self.app.call_from_thread(self.last_error_panel.update, f"[red]{str(e)}[/red]")
                            time.sleep(3)
                            continue

                    earliest_time = exams[0].date
                    for exam in exams[1:]:
                        if exam.date < earliest_time:
                            earliest_time = exam.date

                    self.stats.all_checks += 1

                    if self.stats.earliest_ever_time is None or earliest_time < self.stats.earliest_ever_time:
                        self.stats.earliest_ever_time = earliest_time
                        self.stats.current_earliest_time = earliest_time
                        self.stats.last_found_time = earliest_time
                    elif self.stats.last_found_time is None or earliest_time < self.stats.last_found_time:
                        self.stats.last_found_time = earliest_time
                        self.stats.current_earliest_time = earliest_time
                    else:
                        self.stats.last_found_time = earliest_time

                    df_dt = datetime.strptime(self.cfg.date_from, "%Y-%m-%d")
                    dt_dt = datetime.strptime(self.cfg.date_to, "%Y-%m-%d")
                    hf = datetime.strptime(self.cfg.hour_from, "%H:%M").time()
                    ht = datetime.strptime(self.cfg.hour_to, "%H:%M").time()

                    earliest_matching_exam = None

                    for exam in exams:
                        if (
                            df_dt <= exam.date <= dt_dt and
                            hf <= exam.date.time() <= ht
                        ):
                            if earliest_matching_exam is None or exam.date < earliest_matching_exam.date:
                                earliest_matching_exam = exam

                    if earliest_matching_exam is not None:
                        self.running = False
                        self.app.call_from_thread(
                            self.app.switch_screen,
                            RescheduleScreen(
                                session=self.session,
                                reservation=self.reservation,
                                new_exam=earliest_matching_exam,
                            ),
                        )
                        playsound3.playsound("alert.mp3", False)

                    self.app.call_from_thread(self.update_panels)
                    self.app.call_from_thread(self.last_error_panel.update, "")
                except Exception as e:
                    self.app.call_from_thread(self.last_error_panel.update, f"[red]{str(e)}[/red]")

                time.sleep(15)
        finally:
            self.running = False

    def update_panels(self) -> None:
        turn_panel: StatPanel = self.query_one("#turnstile")
        all_checks_panel: StatPanel = self.query_one("#all_checks")
        earliest_ever_panel: StatPanel = self.query_one("#earliest_ever")
        current_earliest_panel: StatPanel = self.query_one("#current_earliest")
        last_found_panel: StatPanel = self.query_one("#last_found")

        turn_panel.update_value(
            f"{self.session.turnstile_solve_count} (~${self.session.turnstile_solve_count * 1.2 / 1000:.3f})"
        )
        all_checks_panel.update_value(str(self.stats.all_checks))
        earliest_ever_panel.update_value(
            self.stats.earliest_ever_time.strftime("%Y-%m-%d %H:%M")
            if self.stats.earliest_ever_time is not None
            else "-"
        )
        current_earliest_panel.update_value(
            self.stats.current_earliest_time.strftime("%Y-%m-%d %H:%M")
            if self.stats.current_earliest_time is not None
            else "-"
        )
        last_found_panel.update_value(
            self.stats.last_found_time.strftime("%Y-%m-%d %H:%M")
            if self.stats.last_found_time is not None
            else "-"
        )

    def _compute_elapsed_text_safe(self) -> str:
        """Compute short elapsed time like '5m' or '3h10m' since checking started."""
        try:
            app_state: AppState = getattr(self.app, "state")
            if app_state.started_checking_at is None:
                return "0m"
            delta = datetime.now() - app_state.started_checking_at
            if delta.total_seconds() < 0:
                return "0m"
            return self._format_timedelta_short(delta)
        except Exception:
            return "0m"

    def _update_elapsed_banner(self) -> None:
        try:
            elapsed = self._compute_elapsed_text_safe()
            self.query_one("#searching_for", Static).update(f"Searching for ({elapsed})")
        except Exception:
            pass

    @staticmethod
    def _format_timedelta_short(td: timedelta) -> str:
        total = int(td.total_seconds())
        if total <= 0:
            return "0m"
        days, rem = divmod(total, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)

        if days > 0:
            # Show up to 2 units: days and hours
            if hours > 0:
                return f"{days}d{hours}h"
            return f"{days}d"
        if hours > 0:
            if minutes > 0:
                return f"{hours}h{minutes}m"
            return f"{hours}h"
        return f"{minutes}m"

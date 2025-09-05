from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Center, Horizontal
from textual.widgets import Static, Label

from datetime import datetime
import time
import threading

from infocar import InfoCarSession
from widgets.spinner import Spinner

class RescheduleScreen(Screen):
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

        #ticker_container {
            height: auto;
            width: auto;
        }

        #spinner {
            text-style: bold;
        }

        #ticker_text {
            padding-left: 1;
            text-style: bold;
            width: auto;
        }

        .hidden {
            display: none;
        }

        Center {
            content-align: center middle;
            width: auto;
            height: auto;
        }
    """

    def __init__(self, session: InfoCarSession, reservation, new_exam) -> None:
        super().__init__()
        self.session = session
        self.reservation = reservation
        self.new_exam = new_exam

        self.ticker = None
        self.error_panel = None

    def compose(self) -> ComposeResult:
        old_ts = time.strptime(self.reservation['exam']['practice']['date'], "%Y-%m-%dT%H:%M:%S")
        old_date_str = time.strftime("%Y-%m-%d %H:%M", old_ts)
        new_date_str = self.new_exam.date.strftime("%Y-%m-%d %H:%M")

        main_container = Container(
            Center(
                Horizontal(
                    Spinner(id="spinner"),
                    Label(id="ticker_text"),
                    id="ticker_container",
                )
            ),
            Center(Label(f"Old date: {old_date_str}", id="old_date")),
            Center(Label(f"New date: {new_date_str}", id="new_date")),
            Center(Label(id="details_line")),
            Center(Label(id="saving_line")),
            Label(id="error_panel"),
            id="main_container",
        )

        main_container.border_title = "Info-Car Sniper - Rescheduling"
        main_container.border_subtitle = "Ctrl+c exit"

        yield main_container

    def on_mount(self) -> None:
        self.ticker_text = self.query_one("#ticker_text")
        ticker_container = self.query_one("#ticker_container")

        self.error_panel = self.query_one("#error_panel")
        self.ticker_text.update("Rescheduling exam...")

        def do_reschedule():
            try:
                reservation_id = self.reservation['id']
                self.session.reschedule_exam(reservation_id, self.new_exam.id)

                old_ts = time.strptime(self.reservation['exam']['practice']['date'], "%Y-%m-%dT%H:%M:%S")
                old_date_str = time.strftime("%Y-%m-%d %H:%M", old_ts)
                new_date_str = self.new_exam.date.strftime("%Y-%m-%d %H:%M")

                old_dt = datetime.strptime(self.reservation['exam']['practice']['date'], "%Y-%m-%dT%H:%M:%S")
                new_dt = self.new_exam.date
                saved_days = (old_dt - new_dt).days
                saved_days = max(saved_days, 0)

                def show_success():
                    self.query_one("#details_line", Static).update("Check your email for details")
                    self.query_one("#old_date", Static).update(f"Old date: {old_date_str}")
                    self.query_one("#new_date", Static).update(f"New date: {new_date_str}")
                    self.query_one("#saving_line", Static).update(f"With us you are saving {saved_days} days")

                ticker_container.add_class("hidden")

                self.app.call_from_thread(show_success)
            except Exception as e:
                def show_error():
                    self.ticker_text.update("Failed to reschedule an exam.")
                    self.error_panel.update(f"[red]{str(e)}[/red]")
                self.app.call_from_thread(show_error)

        threading.Thread(target=do_reschedule, daemon=True).start()

import os

from dotenv import load_dotenv

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.widget import Widget
from textual.screen import ModalScreen, Screen
from textual.widgets import Tree, Header, Static, Button, Input, Footer, Label
from textual.worker import Worker, WorkerState

from .gridfs_manager import GridFsManager
from .util import escape_markup

class ConnectionScreen(ModalScreen[GridFsManager]):
    """Screen with a dialog to connect to a server"""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Connect to Server...", id="popup_title"),
            Input("mongodb://localhost:27017/", id="connect_str"),
            Button("Connect", variant="primary", id="connect_btn"),
            Button("Cancel", id="cancel_btn"),
            id="connectdialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_btn":
            self.dismiss(None)
        else:
            # start connection attempt
            self.query_one("#connectdialog").loading = True

            conn_str = self.query_one("#connect_str", Input)
            print("Connection string: " + conn_str.value)
            self.do_connection(conn_str.value)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        self.log.info(f"Worker state changed: {event.state}")
        if event.state == WorkerState.SUCCESS:
            self.notify("Connected!", severity="information")
            self.query_one("#connectdialog").loading = False
            
        elif event.state == WorkerState.ERROR:
            self.log.error("Worker failed.")
            self.notify(f"Connection failed: {escape_markup(str(event.worker.error))}", severity="error")
            self.query_one("#connectdialog").loading = False

    @work(exclusive=True, exit_on_error=False)
    async def do_connection(self, connection_string: str):
        try:
            # Create a MongoClient instance
            client = GridFsManager(connection_string)
            # Test the connection
            await client.connect()
            await client.test_connection()
            self.dismiss(client)
        except Exception as e:
            self.app.log.error(f"Connection failed: {e}")
            raise e


class QuitScreen(ModalScreen):
    """Screen with a dialog to quit."""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to quit?", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()

class MongoView(Tree):
    def compose(self) -> ComposeResult:
        # Want a list of the collections in the datastore, where
        # the top level tree element is the collection name
        tree: Tree[str] = Tree("Dune")
        tree.root.expand()
        characters = tree.root.add("Characters", expand=True)
        characters.add_leaf("Paul")
        characters.add_leaf("Jessica")
        characters.add_leaf("Chani")
        yield tree

class GridFsBrowser(App):
    
    TITLE = "GridnightCommander - Disconnected"
    CSS_PATH = "tcss/main.tcss"

    # def on_mount(self):
    #     self.screen.styles.background = "darkblue"

    BINDINGS = [
        ("c", "do_connect", "Connect to server"),
        ("q", "request_quit", "Quit")
    ]

    def compose(self) -> ComposeResult:
        self.log.info("Staring GNC")
        yield Header()
        with Vertical(classes="filetree"):
            yield MongoView("MongoView", classes="borderless")
        yield Static("TEST", classes="preview")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "connect":
            self.title = "GridnightCommander - Connected"
    
    def action_do_connect(self) -> None:
        self.push_screen(ConnectionScreen())        

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())


def main():
    load_dotenv()
    app = GridFsBrowser()
    app.run()


if __name__ == "__main__":
    main()
import os

from dotenv import load_dotenv

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.widget import Widget
from textual.screen import ModalScreen, Screen
from textual.widgets import Tree, Header, Static, Button, Input, Footer, Label

class ConnectionScreen(ModalScreen):
    """Screen with a dialog to connect to a server"""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Connect to Server...", id="popup_title"),
            Input("mongodb://localhost:27017/"),
            Button("Connect", variant="primary", id="connect_btn"),
            Button("Cancel", id="cancel_btn"),
            id="connectdialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_btn":
            self.app.pop_screen()
        else:
            # Do whatever
            self.app.pop_screen()

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

class TreeThing(Tree):
    def compose(self) -> ComposeResult:
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
        yield Header()
        with Vertical(classes="filetree"):
            yield TreeThing("MongoView", classes="borderless")
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
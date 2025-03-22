import os

from dotenv import load_dotenv

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Tree, Header, Static, Button, Input

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
    
    TITLE = "MongoCommander - Disconnected"
    CSS_PATH = "tcss/main.tcss"

    # def on_mount(self):
    #     self.screen.styles.background = "darkblue"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(classes="filetree"):
            yield TreeThing("MongoView", classes="borderless")
            yield Input(placeholder="Connection String")
            yield Button(label="Connect")
        yield Static("TEST", classes="preview")

def main():
    load_dotenv()
    app = GridFsBrowser()
    app.run()


if __name__ == "__main__":
    main()
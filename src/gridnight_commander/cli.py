import os

from dotenv import load_dotenv

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.reactive import reactive
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
            # Use 'gnc-test' database for now (TODO: make this configurable)
            client = GridFsManager(connection_string, db_name='gnc-test')
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

    data = reactive({})
    client: reactive[GridFsManager | None] = reactive(None)

    def watch_client(self, new_client: GridFsManager | None):
        """Called when client reactive property changes"""
        self.app.log.info(f"watch_client called with: {new_client}")
        if new_client is None:
            # Disconnected - show empty tree
            self.reset("GridFS Browser")
        else:
            # Connected - populate tree with buckets and files
            self.app.log.info("Starting tree population worker")
            worker = self._populate_tree_worker(new_client)

    @work(exclusive=True)
    async def _populate_tree_worker(self, manager: GridFsManager):
        """Populate the tree with GridFS buckets and files"""
        try:
            self.app.log.info("Worker started - populating tree")
            # Clear existing tree and set root label
            self.reset("GridFS Browser")
            self.root.expand()

            # Get list of buckets
            buckets = await manager.list_gridfs_buckets()
            self.app.log.info(f"Found {len(buckets)} buckets: {buckets}")

            if not buckets:
                self.root.add_leaf("(no buckets found)")
                return

            # For each bucket, create a node and populate with files
            for bucket_name in buckets:
                files = await manager.list_files_in_bucket(bucket_name)

                # Create bucket node with file count
                file_count = len(files)
                bucket_label = f"{bucket_name}/ ({file_count} files)"
                bucket_node = self.root.add(bucket_label, expand=False)

                if not files:
                    bucket_node.add_leaf("(empty)")
                else:
                    # Add each file as a leaf node
                    for file_info in files:
                        filename = file_info['filename']
                        # Format file size (bytes to KB/MB)
                        size = file_info['length']
                        if size < 1024:
                            size_str = f"{size}B"
                        elif size < 1024 * 1024:
                            size_str = f"{size / 1024:.1f}KB"
                        else:
                            size_str = f"{size / (1024 * 1024):.1f}MB"

                        file_label = f"{filename} ({size_str})"
                        # Store file info as node data for later use
                        file_node = bucket_node.add_leaf(file_label)
                        file_node.data = {
                            'bucket': bucket_name,
                            'file_info': file_info
                        }

        except Exception as e:
            self.app.log.error(f"Error populating tree: {e}")
            self.reset("GridFS Browser")
            self.root.add_leaf(f"Error: {str(e)}")

class GridFsBrowser(App):
    
    TITLE = "GridnightCommander - Disconnected"
    CSS_PATH = "tcss/main.tcss"

    client: reactive[GridFsManager | None] = reactive(None)

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
            yield MongoView("MongoView", classes="borderless", id="mongo_view")
        yield Static("TEST", classes="preview")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "connect":
            pass

    async def action_do_connect(self) -> None:
        client = await self.push_screen(ConnectionScreen())
        if client:
            self.title = "GridnightCommander - Connected"
            self.client = client
            # Directly update the MongoView
            mongo_view = self.query_one("#mongo_view", MongoView)
            mongo_view.client = client

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())


def main():
    load_dotenv()
    app = GridFsBrowser()
    app.run()


if __name__ == "__main__":
    main()
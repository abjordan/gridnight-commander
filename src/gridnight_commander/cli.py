import os
from typing import Any
from pathlib import Path

from dotenv import load_dotenv

from datetime import datetime

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Grid, VerticalScroll
from textual.reactive import var
from textual.widget import Widget
from textual.screen import ModalScreen, Screen
from textual.widgets import Tree, Header, Static, Button, Input, Footer, Label, Markdown, Select
from textual.message import Message as TextualMessage
from textual_fspicker import FileOpen
from rich.syntax import Syntax

from gridnight_commander.gridfs_manager import GridFsManager
from gridnight_commander.util import escape_markup

class ConnectionScreen(ModalScreen[None]):
    """Screen with a dialog to connect to a server"""

    class Connected(TextualMessage):
        """Message sent when connection succeeds"""
        def __init__(self, client: GridFsManager) -> None:
            self.client = client
            super().__init__()

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
            self.dismiss()
        else:
            # start connection attempt
            self.query_one("#connectdialog").loading = True
            conn_str = self.query_one("#connect_str", Input)
            # Run the connection as a background task
            self.run_worker(self._do_connection_async(conn_str.value))

    async def _do_connection_async(self, connection_string: str) -> None:
        """Async connection that posts a message on success"""
        try:
            # Create a MongoClient instance
            # Use 'gnc-test' database for now (TODO: make this configurable)
            client = GridFsManager(connection_string, db_name='gnc-test')
            # Test the connection
            await client.connect()
            await client.test_connection()
            self.notify("Connected!", severity="information")
            # Post message to parent app
            self.post_message(self.Connected(client))
            # Dismiss the dialog
            self.dismiss()
        except Exception as e:
            self.app.log.error(f"Connection failed: {e}")
            self.notify(f"Connection failed: {escape_markup(str(e))}", severity="error")
            self.query_one("#connectdialog").loading = False


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


class UploadDialog(ModalScreen[None]):
    """Screen with a dialog to upload files"""

    class FileUploaded(TextualMessage):
        """Message sent when file upload succeeds"""
        def __init__(self, bucket: str, filename: str) -> None:
            self.bucket = bucket
            self.filename = filename
            super().__init__()

    def __init__(self, buckets: list[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buckets = buckets
        self.selected_file: Path | None = None

    def compose(self) -> ComposeResult:
        # Create bucket options
        bucket_options = [(bucket, bucket) for bucket in self.buckets]

        yield Grid(
            Label("Upload File to GridFS", id="upload_title"),
            Label("Selected File:"),
            Static("No file selected", id="file_display"),
            Button("Browse...", variant="default", id="browse_btn"),
            Label("Bucket:"),
            Select(bucket_options, id="bucket_select", allow_blank=False),
            Label("Filename (optional):"),
            Input(placeholder="Leave blank to use original filename", id="filename_input"),
            Button("Upload", variant="primary", id="upload_btn"),
            Button("Cancel", id="cancel_btn"),
            id="uploaddialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_btn":
            self.dismiss()
        elif event.button.id == "browse_btn":
            # Open file picker - must run in worker
            self.run_worker(self._handle_file_browse())
        elif event.button.id == "upload_btn":
            # Validate file is selected
            if self.selected_file is None:
                self.notify("Please select a file first", severity="error")
                return

            # Start upload
            self.query_one("#uploaddialog").loading = True
            bucket_select = self.query_one("#bucket_select", Select)
            bucket = bucket_select.value
            filename = self.query_one("#filename_input", Input).value or None

            # Validate bucket is selected
            if isinstance(bucket, str):
                # Run upload
                self.run_worker(self._do_upload(str(self.selected_file), bucket, filename))
            else:
                self.notify("Please select a bucket", severity="error")
                self.query_one("#uploaddialog").loading = False

    async def _handle_file_browse(self) -> None:
        """Handle file browsing - must run in worker context"""
        try:
            # Open file picker
            if selected_file := await self.app.push_screen_wait(FileOpen()):
                self.selected_file = selected_file
                # Update display to show selected file
                file_display = self.query_one("#file_display", Static)
                file_display.update(str(selected_file))
        except Exception as e:
            self.app.log.error(f"File browse failed: {e}")
            self.notify(f"Error browsing files: {escape_markup(str(e))}", severity="error")

    async def _do_upload(self, file_path: str, bucket: str, filename: str | None) -> None:
        """Async upload that posts a message on success"""
        try:
            import os

            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Get the GridFsManager from the app
            client = self.app.client # type: ignore
            if client is None:
                raise Exception("Not connected to database")

            # Upload the file
            file_id = await client.upload_file(bucket, file_path, filename)

            uploaded_filename = filename or os.path.basename(file_path)
            self.notify(f"Uploaded {uploaded_filename} to {bucket}", severity="information")

            # Post message to parent app
            self.post_message(self.FileUploaded(bucket, uploaded_filename))

            # Dismiss the dialog
            self.dismiss()
        except Exception as e:
            self.app.log.error(f"Upload failed: {e}")
            self.notify(f"Upload failed: {escape_markup(str(e))}", severity="error")
            self.query_one("#uploaddialog").loading = False


class DeleteConfirmationDialog(ModalScreen[None]):
    """Screen with a dialog to confirm file deletion"""

    class FileDeleted(TextualMessage):
        """Message sent when file deletion succeeds"""
        def __init__(self, bucket: str, filename: str) -> None:
            self.bucket = bucket
            self.filename = filename
            super().__init__()

    def __init__(self, bucket: str, file_id: Any, filename: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bucket = bucket
        self.file_id = file_id
        self.filename = filename

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(f"Delete '{self.filename}' from '{self.bucket}'?", id="delete_question"),
            Label("This action cannot be undone!", classes="warning"),
            Button("Delete", variant="error", id="delete_btn"),
            Button("Cancel", variant="primary", id="cancel_btn"),
            id="deletedialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_btn":
            self.dismiss()
        else:
            # Start deletion
            self.query_one("#deletedialog").loading = True
            self.run_worker(self._do_delete())

    async def _do_delete(self) -> None:
        """Async deletion that posts a message on success"""
        try:
            # Get the GridFsManager from the app - we know it's there, so ignore the warning
            client = self.app.client # pyright: ignore[reportAttributeAccessIssue]
            if client is None:
                raise Exception("Not connected to database")

            # Delete the file
            await client.delete_file(self.bucket, self.file_id)

            self.notify(f"Deleted {self.filename} from {self.bucket}", severity="information")

            # Post message to parent app
            self.post_message(self.FileDeleted(self.bucket, self.filename))

            # Dismiss the dialog
            self.dismiss()
        except Exception as e:
            self.app.log.error(f"Delete failed: {e}")
            self.notify(f"Delete failed: {escape_markup(str(e))}", severity="error")
            self.query_one("#deletedialog").loading = False


class MongoView(Tree):

    client: var[GridFsManager | None] = var(None, init=False)

    def watch_client(self, new_client: GridFsManager | None):
        """Called when client reactive property changes"""
        if new_client is None:
            # Disconnected - show empty tree
            self.reset("GridFS Browser")
        else:
            # Connected - populate tree with buckets and files
            worker = self._populate_tree_worker(new_client)

    def refresh_tree(self):
        """Force refresh the tree with current client"""
        if self.client:
            worker = self._populate_tree_worker(self.client)

    @work(exclusive=True)
    async def _populate_tree_worker(self, manager: GridFsManager):
        """Populate the tree with GridFS buckets and files"""
        try:
            # Clear existing tree and set root label
            self.reset("GridFS Browser")
            self.root.expand()

            # Get list of buckets
            buckets = await manager.list_gridfs_buckets()

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


class FilePreview(Vertical):
    """Widget for displaying file content and metadata"""

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="preview_scroll"):
            yield Static("Select a file to preview", id="preview_content")
        yield Static("", id="preview_metadata")

    def show_file(self, file_data: dict) -> None:
        """Display file content and metadata"""
        content = file_data['content']
        filename = file_data['filename']
        content_type = file_data.get('contentType', 'text/plain')
        length = file_data['length']
        upload_date = file_data['uploadDate']

        # Get the scroll container
        scroll = self.query_one("#preview_scroll", VerticalScroll)

        # Remove all children from scroll container
        scroll.remove_children()

        # Try to decode as text
        try:
            text_content = content.decode('utf-8')

            # Determine if we should use syntax highlighting
            lexer_name = self._get_lexer_for_file(filename)

            if filename.endswith('.md'):
                # Render markdown
                scroll.mount(Markdown(text_content))
            elif lexer_name:
                # Use syntax highlighting for code files
                syntax = Syntax(
                    text_content,
                    lexer_name,
                    line_numbers=True,
                    theme="monokai",
                    word_wrap=False
                )
                scroll.mount(Static(syntax))
            else:
                # Plain text - escape markup to prevent errors
                scroll.mount(Static(escape_markup(text_content)))

        except UnicodeDecodeError:
            # Binary file
            scroll.mount(Static(f"[Binary file - {length} bytes]\nCannot display binary content."))

        # Format metadata
        date_str = upload_date.strftime("%Y-%m-%d %H:%M:%S") if upload_date else "Unknown"
        size_str = self._format_size(length)

        metadata_text = f"\n---\n📄 {filename}\n📦 {size_str}\n🕒 {date_str}"
        if content_type:
            metadata_text += f"\n📋 {content_type}"

        metadata_widget = self.query_one("#preview_metadata", Static)
        metadata_widget.update(metadata_text)

    def _get_lexer_for_file(self, filename: str) -> str | None:
        """Determine the appropriate lexer name for syntax highlighting based on file extension"""
        # Map file extensions to Pygments lexer names
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
            '.fish': 'fish',
            '.ps1': 'powershell',
            '.r': 'r',
            '.sql': 'sql',
            '.html': 'html',
            '.htm': 'html',
            '.xml': 'xml',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
            '.conf': 'ini',
            '.dockerfile': 'docker',
            '.Dockerfile': 'docker',
            '.tex': 'latex',
            '.lua': 'lua',
            '.vim': 'vim',
            '.el': 'elisp',
            '.clj': 'clojure',
            '.ex': 'elixir',
            '.exs': 'elixir',
            '.erl': 'erlang',
            '.hs': 'haskell',
            '.ml': 'ocaml',
            '.pl': 'perl',
            '.pm': 'perl',
        }

        # Get the file extension (lowercase)
        for ext, lexer in extension_map.items():
            if filename.lower().endswith(ext):
                return lexer

        # Special case for Dockerfile
        if filename == 'Dockerfile' or filename.endswith('.dockerfile'):
            return 'docker'

        return None

    def _format_size(self, size: int) -> str:
        """Format byte size to human readable"""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f}KB"
        else:
            return f"{size / (1024 * 1024):.1f}MB"

    def clear(self) -> None:
        """Clear the preview"""
        scroll = self.query_one("#preview_scroll", VerticalScroll)
        scroll.remove_children()
        scroll.mount(Static("Select a file to preview"))

        metadata_widget = self.query_one("#preview_metadata", Static)
        metadata_widget.update("")


class GridFsBrowser(App):
    
    TITLE = "GridnightCommander - Disconnected"
    CSS_PATH = "tcss/main.tcss"

    client: var[GridFsManager | None] = var(None)

    # def on_mount(self):
    #     self.screen.styles.background = "darkblue"

    BINDINGS = [
        ("c", "do_connect", "Connect to server"),
        ("u", "do_upload", "Upload file"),
        ("d", "do_delete", "Delete file"),
        ("q", "request_quit", "Quit")
    ]

    # Track currently selected file for deletion
    selected_file_info: dict | None = None

    def compose(self) -> ComposeResult:
        self.log.info("Staring GNC")
        yield Header()
        with Vertical(classes="filetree"):
            yield MongoView("MongoView", classes="borderless", id="mongo_view")
        yield FilePreview(classes="preview", id="file_preview")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "connect":
            pass

    def action_do_connect(self) -> None:
        """Open the connection dialog"""
        self.push_screen(ConnectionScreen())

    def on_connection_screen_connected(self, message: ConnectionScreen.Connected) -> None:
        """Handle successful connection from ConnectionScreen"""
        self.title = "GridnightCommander - Connected"
        self.client = message.client
        # Update the MongoView with the connected client
        mongo_view = self.query_one("#mongo_view", MongoView)
        mongo_view.client = message.client

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection to preview files"""
        node = event.node

        # Check if node has file data (leaf nodes with file info)
        if hasattr(node, 'data') and node.data and isinstance(node.data, dict):
            if 'file_info' in node.data:
                # This is a file node
                bucket = node.data['bucket']
                file_info = node.data['file_info']
                file_id = file_info['_id']

                # Store selected file info for deletion
                self.selected_file_info = {
                    'bucket': bucket,
                    'file_id': file_id,
                    'filename': file_info['filename']
                }

                # Load and preview the file (worker will be started automatically)
                worker = self._load_file_preview(bucket, file_id)
            else:
                # Not a file node (bucket node), clear selection
                self.selected_file_info = None
        else:
            # No data, clear selection
            self.selected_file_info = None

    @work(exclusive=True)
    async def _load_file_preview(self, bucket: str, file_id: Any) -> None:
        """Load file content and update preview"""
        try:
            if self.client is None:
                return

            # Get the file content
            file_data = await self.client.get_file_content(bucket, file_id)

            if file_data:
                # Update the preview widget
                preview = self.query_one("#file_preview", FilePreview)
                preview.show_file(file_data)
        except Exception as e:
            self.log.error(f"Error loading file preview: {e}")
            self.notify(f"Error loading file: {escape_markup(str(e))}", severity="error")

    async def action_do_upload(self) -> None:
        """Open the upload dialog"""
        if self.client is None:
            self.notify("Not connected to database", severity="warning")
            return

        # Get list of buckets
        try:
            buckets = await self.client.list_gridfs_buckets()
            if not buckets:
                self.notify("No buckets found. Connect to a database with GridFS buckets.", severity="warning")
                return

            self.push_screen(UploadDialog(buckets))
        except Exception as e:
            self.log.error(f"Error getting buckets: {e}")
            self.notify(f"Error: {escape_markup(str(e))}", severity="error")

    def on_upload_dialog_file_uploaded(self, message: UploadDialog.FileUploaded) -> None:
        """Handle successful file upload"""
        # Refresh the tree to show the new file
        mongo_view = self.query_one("#mongo_view", MongoView)
        mongo_view.refresh_tree()

    def action_do_delete(self) -> None:
        """Open the delete confirmation dialog"""
        if self.client is None:
            self.notify("Not connected to database", severity="warning")
            return

        if self.selected_file_info is None:
            self.notify("No file selected. Select a file first.", severity="warning")
            return

        # Open confirmation dialog
        self.push_screen(DeleteConfirmationDialog(
            self.selected_file_info['bucket'],
            self.selected_file_info['file_id'],
            self.selected_file_info['filename']
        ))

    def on_delete_confirmation_dialog_file_deleted(self, message: DeleteConfirmationDialog.FileDeleted) -> None:
        """Handle successful file deletion"""
        # Clear the selected file
        self.selected_file_info = None
        # Clear the preview
        preview = self.query_one("#file_preview", FilePreview)
        preview.clear()
        # Refresh the tree to remove the deleted file
        mongo_view = self.query_one("#mongo_view", MongoView)
        mongo_view.refresh_tree()

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())


def main():
    load_dotenv()
    app = GridFsBrowser()
    app.run()


if __name__ == "__main__":
    main()
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GridNight Commander (gnc) is a terminal-based file manager for MongoDB GridFS, built using the Textual TUI framework. It provides a Midnight Commander-like interface for browsing, uploading, deleting, and previewing files stored in GridFS buckets.

## Development Setup

### Prerequisites
- Python 3.13+ (specified in .python-version)
- uv package manager
- Docker and Docker Compose (for local MongoDB)

### Environment Setup
```bash
# Install dependencies
uv sync

# Copy environment file
cp sample.env .env

# Start MongoDB and mongo-express
docker compose up -d

# Run the application
uv run gnc
# or
python -m gridnight_commander.cli
```

### Development Dependencies
```bash
# Install with dev dependencies
uv sync --extra dev

# This includes textual-dev for development tools
```

## Architecture

### Core Components

**GridFsManager** ([gridfs_manager.py](src/gridnight_commander/gridfs_manager.py))
- Async MongoDB/GridFS client wrapper using Motor (AsyncIOMotorClient)
- Manages database connections and GridFS bucket operations
- Connection timeout: 2s, socket timeout: 20s, server selection timeout: 2s
- Main methods:
  - `connect()`: Establishes async MongoDB connection
  - `test_connection()`: Pings database to verify connectivity
  - `list_gridfs_buckets()`: Finds all GridFS buckets (collections ending in '.files')

**GridFsBrowser** ([cli.py](src/gridnight_commander/cli.py))
- Main Textual App class
- Uses reactive data binding for client state (`reactive[GridFsManager | None]`)
- Key bindings:
  - `c`: Connect to server
  - `u`: Upload file
  - `d`: Delete file
  - `q`: Quit with confirmation dialog
- Layout: Header → File tree (left) → Preview panel (right) → Footer

**ConnectionScreen** ([cli.py](src/gridnight_commander/cli.py))
- Modal screen for server connections
- Uses `@work(exclusive=True, exit_on_error=False)` decorator for async connection
- Handles WorkerState changes (SUCCESS/ERROR) for UI feedback
- Dismisses with GridFsManager instance on successful connection

**MongoView** ([cli.py](src/gridnight_commander/cli.py))
- Textual Tree widget for displaying GridFS buckets and files
- Uses reactive properties: `data` and `client`
- Dynamically populates tree from GridFS buckets and files
- Uses `@work` decorator for async tree population

**UploadDialog** ([cli.py](src/gridnight_commander/cli.py))
- Modal screen for uploading files to GridFS buckets
- Uses `textual-fspicker` library for file selection (FileOpen dialog)
- Workflow: Browse for file → Select bucket → Optional custom filename → Upload
- Validates file selection and bucket before uploading
- Posts FileUploaded message to trigger tree refresh

**DeleteConfirmationDialog** ([cli.py](src/gridnight_commander/cli.py))
- Modal screen for confirming file deletion
- Shows file and bucket name for confirmation
- Posts FileDeleted message to trigger tree refresh and preview clear

**FilePreview** ([cli.py](src/gridnight_commander/cli.py))
- Widget for displaying file content and metadata
- Supports syntax highlighting for code files using Rich's Syntax class
- Recognizes 50+ file extensions (Python, JavaScript, Go, Rust, etc.)
- Uses Monokai theme with line numbers for code
- Markdown files rendered with Markdown widget
- Plain text files displayed with escaped markup
- Shows binary file indicator for non-text files
- Displays metadata: filename, size, upload date, content type

### Styling
- CSS stored in [tcss/main.tcss](src/gridnight_commander/tcss/main.tcss)
- Uses Textual's CSS-like styling system

### Utilities
**escape_markup()** ([util.py](src/gridnight_commander/util.py))
- Escapes square brackets for Textual markup rendering
- Essential for displaying user-provided text that might contain `[` or `]`

## Testing and Data Generation

### Generate Test Data
```bash
# Ensure MongoDB is running via docker compose
docker compose up -d

# Generate test data in 'gnc-test' database
python tests/generate_data.py
```

This creates three GridFS buckets (Dune, Programming, Life Skills) with sample files from [tests/test-data/](tests/test-data/).

## Important Patterns

### Async/Await
- Motor requires async/await for all database operations
- Use `@work` decorator in Textual for background tasks
- Worker state management via `on_worker_state_changed`

### Reactive Data Binding
- Textual's reactive properties propagate changes automatically
- Use `.data_bind(client=GridFsBrowser.client)` to sync reactive values between widgets
- Watch methods (`watch_client`) trigger on reactive property changes

### Modal Screens
- Inherit from `ModalScreen[T]` where T is the return type
- Use `dismiss(value)` to close and return value
- Use `push_screen()` and `await` the result

### Error Handling in Textual
- Use `notify()` for user-facing error messages
- Always escape markup in error messages: `escape_markup(str(error))`
- Log errors via `self.log.error()` or `self.app.log.error()`

## Connection String Format
Default: `mongodb://localhost:27017/`

For authenticated connections (via docker-compose):
`mongodb://devroot:devroot@localhost:27017/`

Environment variables in .env:
- MONGO_ROOT_USER
- MONGO_ROOT_PASSWORD
- MONGO_SERVER
- MONGO_PORT

## External Dependencies

### textual-fspicker
- Provides filesystem picker dialogs for Textual applications
- Used in UploadDialog for file selection
- Returns `Path` objects via `push_screen_wait()` pattern
- FileOpen dialog validates file existence by default
- Will also be useful for download destination selection in future features

### Rich (via Textual)
- Textual is built on Rich and includes it as a dependency
- FilePreview uses Rich's Syntax class for code highlighting
- Supports Pygments lexers for 50+ programming languages
- Configured with Monokai theme and line numbers enabled
- No additional dependency installation required

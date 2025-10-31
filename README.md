# GridNight Commander

A beautiful terminal UI (TUI) for browsing, managing, and previewing files in MongoDB GridFS.

![GridNight Commander Screenshot](docs/screenshot.svg)

## Overview

GridNight Commander (`gnc`) is a [Midnight Commander](https://midnight-commander.org/)-inspired file manager specifically designed for MongoDB GridFS. It provides an intuitive interface for working with GridFS buckets and files directly from your terminal.

### Features

- **Browse GridFS Buckets** - View all GridFS buckets in your MongoDB database with expandable tree navigation
- **File Preview** - Preview file contents with support for:
  - Text files (`.txt`, `.log`, `.csv`, etc.)
  - Markdown files (rendered with formatting)
  - Metadata display (filename, size, upload date, content type)
- **Upload Files** - Add new files to any GridFS bucket with automatic MIME type detection
- **Delete Files** - Remove files from buckets with confirmation dialog
- **Live Connection** - Connect to any MongoDB instance with connection string support
- **Keyboard-Driven** - Fast navigation with intuitive keyboard shortcuts

## Installation

GridNight Commander requires Python 3.13+ and uses [uv](https://github.com/astral-sh/uv) for dependency management.

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/gridnight-commander.git
cd gridnight-commander

# Run with uv (automatically installs dependencies)
uv run gnc
```

### Development Setup

```bash
# Install dependencies
uv sync

# Run the application
uv run gnc

# Run tests
uv run python tests/generate_data.py  # Generate test data
uv run python tests/test_delete.py    # Test deletion functionality
```

## Usage

### Connecting to MongoDB

1. Launch GridNight Commander: `uv run gnc`
2. Press `c` to open the connection dialog
3. Enter your MongoDB connection string (e.g., `mongodb://user:pass@localhost:27017/`)
4. Enter the database name
5. Press `Connect` or hit `Enter`

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `c` | Connect to MongoDB server |
| `u` | Upload a file to selected bucket |
| `d` | Delete selected file (with confirmation) |
| `↑`/`↓` | Navigate tree |
| `Enter` | Expand/collapse bucket |
| `q` | Quit application |

### Browsing Files

- Use arrow keys to navigate the tree
- Press `Enter` to expand/collapse buckets
- Select a file to preview its contents in the right pane
- File metadata appears at the bottom of the preview

### Uploading Files

1. Press `u` to open the upload dialog
2. Enter the local file path
3. Select the target GridFS bucket from the dropdown
4. Optionally override the filename
5. Press `Upload` or hit `Enter`

### Deleting Files

1. Select a file in the tree
2. Press `d` to open the delete confirmation dialog
3. Confirm deletion
4. The tree refreshes automatically

## Architecture

GridNight Commander is built with:

- **[Textual](https://textual.textualize.io/)** - Modern Python TUI framework
- **[Motor](https://motor.readthedocs.io/)** - Async MongoDB driver
- **[Rich](https://rich.readthedocs.io/)** - Beautiful terminal formatting and Markdown rendering

### Project Structure

```
gridnight-commander/
├── src/gridnight_commander/
│   ├── cli.py              # Main application and UI components
│   ├── gridfs_manager.py   # MongoDB/GridFS operations
│   └── util.py             # Utility functions
├── tests/
│   ├── generate_data.py    # Test data generator
│   └── test_delete.py      # Deletion tests
├── test-data/              # Sample files for testing
└── docs/                   # Documentation and screenshots
```

## Development

### Running Tests

Start MongoDB for testing:

```bash
docker compose up -d
```

Generate test data:

```bash
uv run python tests/generate_data.py
```

Run the application:

```bash
uv run gnc
```

Connect to the test database:
- Connection String: `mongodb://devroot:devroot@localhost:27017/`
- Database: `gnc-test`

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Configuration

GridNight Commander uses environment variables for MongoDB connection defaults. Create a `.env` file:

```env
MONGO_ROOT_USER=devroot
MONGO_ROOT_PASSWORD=devroot
MONGO_SERVER=localhost
MONGO_PORT=27017
```

## Roadmap

Current functionality includes all core features. Future enhancements may include:

- File download functionality
- Advanced search/filter
- Bucket statistics (file count, total size)
- Connection profiles for quick switching
- File selection highlighting improvements

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed development stages.

## License

[Your license here]

## Credits

Built with [Claude Code](https://claude.com/claude-code)

"""
Shared pytest fixtures for GridNight Commander tests.

Fixture tiers
─────────────
disconnected_manager
    A GridFsManager whose connect() has never been called (db is None).
    Use this to test the "not connected" guard clauses without any I/O.

connected_manager
    A GridFsManager whose db attribute is replaced with an AsyncMock.
    Use this to test method logic (bucket filtering, metadata mapping, etc.)
    without a real MongoDB instance.

live_manager  [integration]
    A GridFsManager connected to a real MongoDB.
    Only runs when --run-integration is passed or MONGO_INTEGRATION_TESTS=1
    is set in the environment.  Requires a running MongoDB accessible via
    the MONGO_* environment variables (or their defaults).
"""

import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from dotenv import load_dotenv

from gridnight_commander.gridfs_manager import GridFsManager


# ---------------------------------------------------------------------------
# Disconnected fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def disconnected_manager() -> GridFsManager:
    """GridFsManager with db=None (connect() never called)."""
    return GridFsManager("mongodb://localhost:27017/", db_name="test")


# ---------------------------------------------------------------------------
# Mocked-db fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def connected_manager() -> GridFsManager:
    """
    GridFsManager with db replaced by an AsyncMock.

    The mock exposes:
      manager.db.list_collection_names   – AsyncMock, default returns []
      manager.db.command                 – AsyncMock, default returns {"ok": 1}

    Individual tests can override return values:
        connected_manager.db.list_collection_names.return_value = ["fs.files"]
    """
    manager = GridFsManager("mongodb://localhost:27017/", db_name="test")
    mock_db = AsyncMock()
    mock_db.list_collection_names = AsyncMock(return_value=[])
    mock_db.command = AsyncMock(return_value={"ok": 1})
    manager.db = mock_db
    return manager


# ---------------------------------------------------------------------------
# Integration fixture (requires live MongoDB)
# ---------------------------------------------------------------------------

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run tests that require a live MongoDB connection.",
    )


def _integration_enabled(config: pytest.Config) -> bool:
    return (
        config.getoption("--run-integration", default=False)
        or os.getenv("MONGO_INTEGRATION_TESTS", "0") == "1"
    )


@pytest_asyncio.fixture
async def live_manager(request: pytest.FixtureRequest) -> GridFsManager:
    """
    GridFsManager connected to a real MongoDB instance.

    Skipped automatically unless --run-integration is supplied or
    MONGO_INTEGRATION_TESTS=1 is set.
    """
    if not _integration_enabled(request.config):
        pytest.skip("Integration tests disabled. Pass --run-integration to enable.")

    load_dotenv()
    user = os.getenv("MONGO_ROOT_USER", "")
    passwd = os.getenv("MONGO_ROOT_PASSWORD", "")
    server = os.getenv("MONGO_SERVER", "localhost")
    port = os.getenv("MONGO_PORT", "27017")

    if user and passwd:
        connection_string = f"mongodb://{user}:{passwd}@{server}:{port}/"
    else:
        connection_string = f"mongodb://{server}:{port}/"

    manager = GridFsManager(connection_string, db_name="gnc-test")
    await manager.connect()
    return manager

"""
Unit tests for GridFsManager.

Mocking strategy
────────────────
• Guard-clause tests (db is None) use the ``disconnected_manager`` fixture.
• Logic tests use the ``connected_manager`` fixture, whose ``db`` attribute is
  already an AsyncMock.
• Methods that create an AsyncIOMotorGridFSBucket internally are covered by
  patching ``gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket``
  so no real Motor I/O occurs.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

from gridnight_commander.gridfs_manager import GridFsManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _aiter(items):
    """Async generator – used to mock Motor async cursors."""
    for item in items:
        yield item


def _make_grid_file(
    file_id="507f1f77bcf86cd799439011",
    filename="test.txt",
    length=1024,
    upload_date=None,
    metadata=None,
):
    """Return a MagicMock shaped like a Motor GridOut document."""
    f = MagicMock()
    f._id = file_id
    f.filename = filename
    f.length = length
    f.upload_date = upload_date or datetime(2024, 1, 1, 12, 0, 0)
    f.metadata = metadata
    return f


def _make_grid_out(content=b"data", filename="file.txt", length=None,
                   upload_date=None, metadata=None):
    """Return an AsyncMock shaped like a Motor GridOut stream."""
    grid_out = AsyncMock()
    grid_out.read = AsyncMock(return_value=content)
    grid_out.filename = filename
    grid_out.length = length if length is not None else len(content)
    grid_out.upload_date = upload_date or datetime(2024, 1, 1)
    grid_out.metadata = metadata
    return grid_out


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

class TestInit:
    def test_stores_connection_string(self):
        mgr = GridFsManager("mongodb://host:27017/")
        assert mgr.connection_string == "mongodb://host:27017/"

    def test_default_db_name_is_test(self):
        mgr = GridFsManager("mongodb://host/")
        assert mgr.db_name == "test"

    def test_custom_db_name(self):
        mgr = GridFsManager("mongodb://host/", db_name="production")
        assert mgr.db_name == "production"

    def test_db_is_none_before_connect(self):
        mgr = GridFsManager("mongodb://host/")
        assert mgr.db is None


# ---------------------------------------------------------------------------
# connect()
# ---------------------------------------------------------------------------

class TestConnect:
    async def test_connect_sets_db_to_non_none(self, disconnected_manager):
        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorClient") as mock_client:
            # Simulate client[db_name] returning a mock database object
            mock_client.return_value = {"test": MagicMock()}
            await disconnected_manager.connect()

        assert disconnected_manager.db is not None

    async def test_connect_uses_connection_string(self, disconnected_manager):
        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorClient") as mock_client:
            mock_client.return_value = {"test": MagicMock()}
            await disconnected_manager.connect()

        mock_client.assert_called_once()
        args, kwargs = mock_client.call_args
        assert args[0] == disconnected_manager.connection_string

    async def test_connect_passes_timeout_settings(self, disconnected_manager):
        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorClient") as mock_client:
            mock_client.return_value = {"test": MagicMock()}
            await disconnected_manager.connect()

        _, kwargs = mock_client.call_args
        assert kwargs["connectTimeoutMS"] == 2000
        assert kwargs["socketTimeoutMS"] == 20000
        assert kwargs["serverSelectionTimeoutMS"] == 2000


# ---------------------------------------------------------------------------
# test_connection()
# ---------------------------------------------------------------------------

class TestTestConnection:
    async def test_returns_false_when_db_is_none(self, disconnected_manager):
        result = await disconnected_manager.test_connection()
        assert result is False

    async def test_returns_true_on_successful_ping(self, connected_manager):
        connected_manager.db.command.return_value = {"ok": 1}
        result = await connected_manager.test_connection()
        assert result is True

    async def test_calls_ping_command(self, connected_manager):
        await connected_manager.test_connection()
        connected_manager.db.command.assert_awaited_once_with("ping")

    async def test_raises_exception_on_ping_failure(self, connected_manager):
        connected_manager.db.command.side_effect = Exception("connection refused")
        with pytest.raises(Exception, match="connection refused"):
            await connected_manager.test_connection()

    async def test_does_not_swallow_exception(self, connected_manager):
        """The exception from db.command must propagate, not be silenced."""
        connected_manager.db.command.side_effect = RuntimeError("timeout")
        with pytest.raises(RuntimeError):
            await connected_manager.test_connection()


# ---------------------------------------------------------------------------
# list_gridfs_buckets()
# ---------------------------------------------------------------------------

class TestListGridfsBuckets:
    async def test_returns_empty_list_when_disconnected(self, disconnected_manager):
        result = await disconnected_manager.list_gridfs_buckets()
        assert result == []

    async def test_returns_empty_when_no_files_collections(self, connected_manager):
        connected_manager.db.list_collection_names.return_value = [
            "system.users", "products", "orders"
        ]
        result = await connected_manager.list_gridfs_buckets()
        assert result == []

    async def test_strips_files_suffix_from_bucket_name(self, connected_manager):
        connected_manager.db.list_collection_names.return_value = ["fs.files", "fs.chunks"]
        result = await connected_manager.list_gridfs_buckets()
        assert result == ["fs"]

    async def test_returns_multiple_buckets(self, connected_manager):
        connected_manager.db.list_collection_names.return_value = [
            "Dune.files", "Dune.chunks",
            "Programming.files", "Programming.chunks",
        ]
        result = await connected_manager.list_gridfs_buckets()
        assert sorted(result) == ["Dune", "Programming"]

    async def test_ignores_collections_containing_but_not_ending_in_files(self, connected_manager):
        connected_manager.db.list_collection_names.return_value = [
            "myfiles",       # does not end with .files
            "files.backup",  # does not end with .files
        ]
        result = await connected_manager.list_gridfs_buckets()
        assert result == []

    async def test_only_returns_files_collections_not_chunks(self, connected_manager):
        connected_manager.db.list_collection_names.return_value = [
            "media.files", "media.chunks"
        ]
        result = await connected_manager.list_gridfs_buckets()
        assert len(result) == 1
        assert result[0] == "media"

    async def test_empty_database_returns_empty(self, connected_manager):
        connected_manager.db.list_collection_names.return_value = []
        result = await connected_manager.list_gridfs_buckets()
        assert result == []


# ---------------------------------------------------------------------------
# list_files_in_bucket()
# ---------------------------------------------------------------------------

class TestListFilesInBucket:
    async def test_returns_empty_list_when_disconnected(self, disconnected_manager):
        result = await disconnected_manager.list_files_in_bucket("fs")
        assert result == []

    async def test_returns_empty_for_empty_bucket(self, connected_manager):
        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = MagicMock()
            mock_bucket.find.return_value = _aiter([])
            mock_cls.return_value = mock_bucket

            result = await connected_manager.list_files_in_bucket("fs")

        assert result == []

    async def test_returns_file_metadata(self, connected_manager):
        upload_date = datetime(2024, 6, 15)
        grid_file = _make_grid_file(
            file_id="abc123",
            filename="notes.txt",
            length=512,
            upload_date=upload_date,
            metadata={"contentType": "text/plain"},
        )

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = MagicMock()
            mock_bucket.find.return_value = _aiter([grid_file])
            mock_cls.return_value = mock_bucket

            result = await connected_manager.list_files_in_bucket("fs")

        assert len(result) == 1
        assert result[0]["_id"] == "abc123"
        assert result[0]["filename"] == "notes.txt"
        assert result[0]["length"] == 512
        assert result[0]["uploadDate"] == upload_date
        assert result[0]["metadata"] == {"contentType": "text/plain"}

    async def test_null_metadata_becomes_empty_dict(self, connected_manager):
        grid_file = _make_grid_file(metadata=None)

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = MagicMock()
            mock_bucket.find.return_value = _aiter([grid_file])
            mock_cls.return_value = mock_bucket

            result = await connected_manager.list_files_in_bucket("fs")

        assert result[0]["metadata"] == {}

    async def test_returns_all_files(self, connected_manager):
        files = [
            _make_grid_file(file_id=str(i), filename=f"file{i}.txt")
            for i in range(5)
        ]

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = MagicMock()
            mock_bucket.find.return_value = _aiter(files)
            mock_cls.return_value = mock_bucket

            result = await connected_manager.list_files_in_bucket("fs")

        assert len(result) == 5

    async def test_passes_bucket_name_to_constructor(self, connected_manager):
        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = MagicMock()
            mock_bucket.find.return_value = _aiter([])
            mock_cls.return_value = mock_bucket

            await connected_manager.list_files_in_bucket("Dune")

        mock_cls.assert_called_once_with(connected_manager.db, bucket_name="Dune")


# ---------------------------------------------------------------------------
# get_file_content()
# ---------------------------------------------------------------------------

class TestGetFileContent:
    async def test_returns_none_when_disconnected(self, disconnected_manager):
        result = await disconnected_manager.get_file_content("fs", "file_id")
        assert result is None

    async def test_returns_content_and_metadata(self, connected_manager):
        upload_date = datetime(2024, 3, 10)
        grid_out = _make_grid_out(
            content=b"hello world",
            filename="hello.txt",
            upload_date=upload_date,
            metadata={"contentType": "text/plain"},
        )

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.open_download_stream.return_value = grid_out
            mock_cls.return_value = mock_bucket

            result = await connected_manager.get_file_content("fs", "file_id")

        assert result["content"] == b"hello world"
        assert result["filename"] == "hello.txt"
        assert result["length"] == 11
        assert result["uploadDate"] == upload_date
        assert result["contentType"] == "text/plain"
        assert result["metadata"] == {"contentType": "text/plain"}

    async def test_content_type_none_when_metadata_is_none(self, connected_manager):
        grid_out = _make_grid_out(content=b"\x89PNG", filename="image.png", metadata=None)

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.open_download_stream.return_value = grid_out
            mock_cls.return_value = mock_bucket

            result = await connected_manager.get_file_content("fs", "id")

        assert result["contentType"] is None
        assert result["metadata"] == {}

    async def test_content_type_none_when_key_absent_from_metadata(self, connected_manager):
        grid_out = _make_grid_out(metadata={"custom": "value"})

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.open_download_stream.return_value = grid_out
            mock_cls.return_value = mock_bucket

            result = await connected_manager.get_file_content("fs", "id")

        assert result["contentType"] is None

    async def test_raises_on_stream_error(self, connected_manager):
        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.open_download_stream.side_effect = Exception("file not found")
            mock_cls.return_value = mock_bucket

            with pytest.raises(Exception, match="file not found"):
                await connected_manager.get_file_content("fs", "bad_id")

    async def test_passes_file_id_to_open_download_stream(self, connected_manager):
        grid_out = _make_grid_out()

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.open_download_stream.return_value = grid_out
            mock_cls.return_value = mock_bucket

            await connected_manager.get_file_content("fs", "target_id")

        mock_bucket.open_download_stream.assert_awaited_once_with("target_id")


# ---------------------------------------------------------------------------
# upload_file()
# ---------------------------------------------------------------------------

class TestUploadFile:
    async def test_raises_when_disconnected(self, disconnected_manager, tmp_path):
        local_file = tmp_path / "upload.txt"
        local_file.write_bytes(b"content")

        with pytest.raises(Exception, match="Not connected"):
            await disconnected_manager.upload_file("fs", str(local_file))

    async def test_returns_file_id(self, connected_manager, tmp_path):
        local_file = tmp_path / "data.txt"
        local_file.write_bytes(b"hello")

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.upload_from_stream.return_value = "new_file_id"
            mock_cls.return_value = mock_bucket

            result = await connected_manager.upload_file("fs", str(local_file))

        assert result == "new_file_id"

    async def test_uses_basename_when_filename_not_provided(self, connected_manager, tmp_path):
        local_file = tmp_path / "report.pdf"
        local_file.write_bytes(b"%PDF")

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.upload_from_stream.return_value = "id"
            mock_cls.return_value = mock_bucket

            await connected_manager.upload_file("fs", str(local_file))
            name_arg = mock_bucket.upload_from_stream.call_args[0][0]

        assert name_arg == "report.pdf"

    async def test_uses_custom_filename_when_provided(self, connected_manager, tmp_path):
        local_file = tmp_path / "tmp12345"
        local_file.write_bytes(b"data")

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.upload_from_stream.return_value = "id"
            mock_cls.return_value = mock_bucket

            await connected_manager.upload_file("fs", str(local_file), filename="custom.txt")
            name_arg = mock_bucket.upload_from_stream.call_args[0][0]

        assert name_arg == "custom.txt"

    async def test_uploads_file_content(self, connected_manager, tmp_path):
        local_file = tmp_path / "data.bin"
        local_file.write_bytes(b"\x00\x01\x02\x03")

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.upload_from_stream.return_value = "id"
            mock_cls.return_value = mock_bucket

            await connected_manager.upload_file("fs", str(local_file))
            content_arg = mock_bucket.upload_from_stream.call_args[0][1]

        assert content_arg == b"\x00\x01\x02\x03"

    async def test_detects_html_mime_type(self, connected_manager, tmp_path):
        local_file = tmp_path / "page.html"
        local_file.write_bytes(b"<html/>")

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.upload_from_stream.return_value = "id"
            mock_cls.return_value = mock_bucket

            await connected_manager.upload_file("fs", str(local_file))
            metadata = mock_bucket.upload_from_stream.call_args[1]["metadata"]

        assert metadata.get("contentType") == "text/html"

    async def test_no_content_type_in_metadata_for_unknown_extension(self, connected_manager, tmp_path):
        local_file = tmp_path / "data.xyzunknown"
        local_file.write_bytes(b"raw")

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.upload_from_stream.return_value = "id"
            mock_cls.return_value = mock_bucket

            await connected_manager.upload_file("fs", str(local_file))
            metadata = mock_bucket.upload_from_stream.call_args[1]["metadata"]

        assert "contentType" not in metadata

    async def test_raises_when_local_file_is_missing(self, connected_manager):
        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket"):
            with pytest.raises(FileNotFoundError):
                await connected_manager.upload_file("fs", "/nonexistent/path/file.txt")

    async def test_raises_on_gridfs_upload_error(self, connected_manager, tmp_path):
        local_file = tmp_path / "file.txt"
        local_file.write_bytes(b"content")

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.upload_from_stream.side_effect = Exception("disk full")
            mock_cls.return_value = mock_bucket

            with pytest.raises(Exception, match="disk full"):
                await connected_manager.upload_file("fs", str(local_file))

    async def test_passes_bucket_name_to_constructor(self, connected_manager, tmp_path):
        local_file = tmp_path / "f.txt"
        local_file.write_bytes(b"x")

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.upload_from_stream.return_value = "id"
            mock_cls.return_value = mock_bucket

            await connected_manager.upload_file("archive", str(local_file))

        mock_cls.assert_called_once_with(connected_manager.db, bucket_name="archive")


# ---------------------------------------------------------------------------
# delete_file()
# ---------------------------------------------------------------------------

class TestDeleteFile:
    async def test_raises_when_disconnected(self, disconnected_manager):
        with pytest.raises(Exception, match="Not connected"):
            await disconnected_manager.delete_file("fs", "file_id")

    async def test_calls_bucket_delete_with_file_id(self, connected_manager):
        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_cls.return_value = mock_bucket

            await connected_manager.delete_file("fs", "target_id")

        mock_bucket.delete.assert_awaited_once_with("target_id")

    async def test_passes_bucket_name_to_constructor(self, connected_manager):
        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_cls.return_value = mock_bucket

            await connected_manager.delete_file("Dune", "file_id")

        mock_cls.assert_called_once_with(connected_manager.db, bucket_name="Dune")

    async def test_raises_on_delete_error(self, connected_manager):
        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.delete.side_effect = Exception("file not found")
            mock_cls.return_value = mock_bucket

            with pytest.raises(Exception, match="file not found"):
                await connected_manager.delete_file("fs", "bad_id")

    async def test_returns_none_on_success(self, connected_manager):
        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_cls.return_value = mock_bucket

            result = await connected_manager.delete_file("fs", "file_id")

        assert result is None


# ---------------------------------------------------------------------------
# download_file()
# ---------------------------------------------------------------------------

class TestDownloadFile:
    async def test_raises_when_disconnected(self, disconnected_manager, tmp_path):
        dest = str(tmp_path / "out.txt")
        with pytest.raises(Exception, match="Not connected"):
            await disconnected_manager.download_file("fs", "file_id", dest)

    async def test_writes_content_to_destination(self, connected_manager, tmp_path):
        dest = tmp_path / "output.txt"
        grid_out = _make_grid_out(content=b"file content here")

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.open_download_stream.return_value = grid_out
            mock_cls.return_value = mock_bucket

            await connected_manager.download_file("fs", "file_id", str(dest))

        assert dest.read_bytes() == b"file content here"

    async def test_raises_on_stream_error(self, connected_manager, tmp_path):
        dest = str(tmp_path / "out.txt")

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.open_download_stream.side_effect = Exception("stream error")
            mock_cls.return_value = mock_bucket

            with pytest.raises(Exception, match="stream error"):
                await connected_manager.download_file("fs", "file_id", dest)

    async def test_passes_correct_bucket_name_and_file_id(self, connected_manager, tmp_path):
        dest = tmp_path / "out.bin"
        grid_out = _make_grid_out(content=b"bytes")

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.open_download_stream.return_value = grid_out
            mock_cls.return_value = mock_bucket

            await connected_manager.download_file("Dune", "specific_id", str(dest))

        mock_cls.assert_called_once_with(connected_manager.db, bucket_name="Dune")
        mock_bucket.open_download_stream.assert_awaited_once_with("specific_id")

    async def test_creates_file_at_destination_path(self, connected_manager, tmp_path):
        dest = tmp_path / "subdir" / "output.bin"
        dest.parent.mkdir()
        grid_out = _make_grid_out(content=b"binary")

        with patch("gridnight_commander.gridfs_manager.AsyncIOMotorGridFSBucket") as mock_cls:
            mock_bucket = AsyncMock()
            mock_bucket.open_download_stream.return_value = grid_out
            mock_cls.return_value = mock_bucket

            await connected_manager.download_file("fs", "id", str(dest))

        assert dest.exists()

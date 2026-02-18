"""
Integration tests for GridFsManager.delete_file().

These tests require a live MongoDB connection.  They are skipped by default;
pass --run-integration (or set MONGO_INTEGRATION_TESTS=1) to enable them.

The tests are self-contained: each one uploads a temporary file, operates
on it, and cleans up after itself, so they do not depend on pre-existing
data in the database.
"""

import pytest
import tempfile
import os
from pathlib import Path


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_BUCKET = "gnc-integration-test"


async def _upload_temp_file(manager, content: bytes = b"test content", filename: str = "test.txt") -> str:
    """Upload a throwaway file and return its file_id."""
    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as f:
        f.write(content)
        tmp_path = f.name
    try:
        file_id = await manager.upload_file(TEST_BUCKET, tmp_path, filename=filename)
    finally:
        os.unlink(tmp_path)
    return file_id


# ---------------------------------------------------------------------------
# delete_file() integration tests
# ---------------------------------------------------------------------------

async def test_delete_removes_file_from_bucket(live_manager):
    """Uploaded file is absent from the bucket after deletion."""
    file_id = await _upload_temp_file(live_manager, b"to be deleted", "delete_me.txt")

    files_before = await live_manager.list_files_in_bucket(TEST_BUCKET)
    ids_before = [f["_id"] for f in files_before]
    assert file_id in ids_before, "File should exist before deletion"

    await live_manager.delete_file(TEST_BUCKET, file_id)

    files_after = await live_manager.list_files_in_bucket(TEST_BUCKET)
    ids_after = [f["_id"] for f in files_after]
    assert file_id not in ids_after, "File should be absent after deletion"


async def test_delete_reduces_file_count_by_one(live_manager):
    """Bucket file count decreases by exactly 1 after a single deletion."""
    file_id = await _upload_temp_file(live_manager, b"count test", "count_test.txt")

    files_before = await live_manager.list_files_in_bucket(TEST_BUCKET)
    count_before = len(files_before)

    await live_manager.delete_file(TEST_BUCKET, file_id)

    files_after = await live_manager.list_files_in_bucket(TEST_BUCKET)
    assert len(files_after) == count_before - 1


async def test_delete_other_files_unaffected(live_manager):
    """Deleting one file leaves other files in the bucket intact."""
    id_keep = await _upload_temp_file(live_manager, b"keep me", "keep.txt")
    id_delete = await _upload_temp_file(live_manager, b"delete me", "delete.txt")

    await live_manager.delete_file(TEST_BUCKET, id_delete)

    remaining_ids = [f["_id"] for f in await live_manager.list_files_in_bucket(TEST_BUCKET)]
    assert id_keep in remaining_ids, "Sibling file should still exist"
    assert id_delete not in remaining_ids, "Deleted file should be gone"

    # Cleanup
    await live_manager.delete_file(TEST_BUCKET, id_keep)


async def test_delete_nonexistent_file_raises(live_manager):
    """Deleting a file ID that does not exist raises an exception."""
    from bson import ObjectId
    fake_id = ObjectId()

    with pytest.raises(Exception):
        await live_manager.delete_file(TEST_BUCKET, fake_id)

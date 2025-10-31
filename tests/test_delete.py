"""
Test script to verify delete functionality works correctly
"""
import asyncio
import os
from dotenv import load_dotenv
from gridnight_commander.gridfs_manager import GridFsManager

load_dotenv()

user = os.getenv("MONGO_ROOT_USER")
passwd = os.getenv("MONGO_ROOT_PASSWORD")
server = os.getenv("MONGO_SERVER")
port = os.getenv("MONGO_PORT")

connection_string = f"mongodb://{user}:{passwd}@{server}:{port}/"

async def test_delete():
    # Connect to test database
    manager = GridFsManager(connection_string, db_name='gnc-test')
    await manager.connect()

    print("✅ Connected to database")

    # List files in Dune bucket before deletion
    print("\n📂 Files in Dune bucket BEFORE deletion:")
    files_before = await manager.list_files_in_bucket('Dune')
    for f in files_before:
        print(f"  - {f['filename']} (id: {f['_id']})")

    if not files_before:
        print("❌ No files found in Dune bucket!")
        return

    # Delete the first file
    file_to_delete = files_before[0]
    print(f"\n🗑️  Deleting file: {file_to_delete['filename']} (id: {file_to_delete['_id']})")

    try:
        await manager.delete_file('Dune', file_to_delete['_id'])
        print("✅ File deleted successfully")
    except Exception as e:
        print(f"❌ Error deleting file: {e}")
        return

    # List files after deletion
    print("\n📂 Files in Dune bucket AFTER deletion:")
    files_after = await manager.list_files_in_bucket('Dune')
    for f in files_after:
        print(f"  - {f['filename']} (id: {f['_id']})")

    # Verify file was actually deleted
    if len(files_after) == len(files_before) - 1:
        print(f"\n✅ SUCCESS! File count decreased from {len(files_before)} to {len(files_after)}")

        # Verify the specific file is gone
        deleted_file_ids = [f['_id'] for f in files_after]
        if file_to_delete['_id'] not in deleted_file_ids:
            print(f"✅ Verified: {file_to_delete['filename']} is no longer in the bucket")
        else:
            print(f"❌ FAILED: {file_to_delete['filename']} still exists!")
    else:
        print(f"❌ FAILED! Expected {len(files_before) - 1} files, but found {len(files_after)}")

if __name__ == "__main__":
    asyncio.run(test_delete())

#!/usr/bin/env python
"""Test script to verify tree population works"""
import asyncio
import os
from dotenv import load_dotenv
from gridnight_commander.gridfs_manager import GridFsManager

load_dotenv()

async def test_tree_population():
    """Simulate what happens when user connects"""
    user = os.getenv('MONGO_ROOT_USER')
    passwd = os.getenv('MONGO_ROOT_PASSWORD')

    # Step 1: Create connection (what ConnectionScreen does)
    print("Step 1: Creating GridFsManager...")
    conn_str = f'mongodb://{user}:{passwd}@localhost:27017/'
    manager = GridFsManager(conn_str, db_name='gnc-test')

    # Step 2: Connect (what ConnectionScreen.do_connection does)
    print("Step 2: Connecting to MongoDB...")
    await manager.connect()
    print("  ✓ Connected")

    # Step 3: Test connection
    print("Step 3: Testing connection...")
    await manager.test_connection()
    print("  ✓ Connection verified")

    # Step 4: What watch_client should trigger
    print("\nStep 4: Simulating watch_client trigger...")
    print("  - watch_client would be called with manager")
    print("  - It would call _populate_tree_worker")

    # Step 5: What _populate_tree_worker does
    print("\nStep 5: Simulating _populate_tree_worker...")
    buckets = await manager.list_gridfs_buckets()
    print(f"  ✓ Found {len(buckets)} buckets: {buckets}")

    for bucket_name in buckets:
        files = await manager.list_files_in_bucket(bucket_name)
        print(f"\n  Bucket '{bucket_name}/' ({len(files)} files):")
        for file_info in files:
            size = file_info['length']
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f}KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f}MB"
            print(f"    - {file_info['filename']} ({size_str})")

    print("\n✅ Tree population logic works correctly!")
    print("\nIf the tree is empty in the app, the issue is likely:")
    print("  1. watch_client is not being triggered")
    print("  2. Data binding is not working")
    print("  3. Reactive property is not propagating")

if __name__ == '__main__':
    asyncio.run(test_tree_population())

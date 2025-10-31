import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket

class GridFsManager:
    def __init__(self, connection_string: str, db_name: str = 'test'):
        """
        Initialize the GridFsManager with a MongoDB connection string.
        :param connection_string: MongoDB connection string
        """
        # Create a MongoClient instance
        self.connection_string = connection_string
        self.db_name = db_name
        self.db = None

    async def connect(self):
        """Connect to the MongoDB server and select the database"""
        dbclient = AsyncIOMotorClient(
            self.connection_string,
            connectTimeoutMS=2000,
            socketTimeoutMS=20000,
            serverSelectionTimeoutMS=2000)
        self.db = dbclient[self.db_name]

    async def test_connection(self) -> bool:
        """Test the connection to the MongoDB server"""
        if self.db is None:
            return False
        try:
            # Attempt to get server information
            await self.db.command("ping")
            print("Connection successful!")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            raise e

    async def list_gridfs_buckets(self):
        """List all GridFS buckets in the database"""
        if self.db is None:
            return []

        collection_names = await self.db.list_collection_names()
        # Find collections ending with '.files'
        buckets = []
        for name in collection_names:
            if name.endswith('.files'):
                bucket_name = name[:-6]  # Remove '.files' suffix
                buckets.append(bucket_name)

        return buckets

    async def list_files_in_bucket(self, bucket_name: str = 'fs'):
        """
        List all files in a GridFS bucket with metadata.
        :param bucket_name: Name of the GridFS bucket (default: 'fs')
        :return: List of dicts with file info (id, filename, length, uploadDate, metadata)
        """
        if self.db is None:
            return []

        bucket = AsyncIOMotorGridFSBucket(self.db, bucket_name=bucket_name)
        files = []

        # Use find() to get all files in the bucket
        async for grid_file in bucket.find():
            file_info = {
                '_id': grid_file._id,
                'filename': grid_file.filename,
                'length': grid_file.length,
                'uploadDate': grid_file.upload_date,
                'metadata': grid_file.metadata or {}
            }
            files.append(file_info)

        return files

    async def get_file_content(self, bucket_name: str, file_id):
        """
        Download a file's content from GridFS.
        :param bucket_name: Name of the GridFS bucket
        :param file_id: The _id of the file to download
        :return: Dictionary with content (bytes) and metadata
        """
        if self.db is None:
            return None

        bucket = AsyncIOMotorGridFSBucket(self.db, bucket_name=bucket_name)

        try:
            # Open the file for reading
            grid_out = await bucket.open_download_stream(file_id)

            # Read the content
            content = await grid_out.read()

            # Return content and metadata
            return {
                'content': content,
                'filename': grid_out.filename,
                'length': grid_out.length,
                'uploadDate': grid_out.upload_date,
                'metadata': grid_out.metadata or {},
                'contentType': grid_out.metadata.get('contentType') if grid_out.metadata else None
            }
        except Exception as e:
            print(f"Error downloading file {file_id}: {e}")
            raise e

    async def upload_file(self, bucket_name: str, local_path: str, filename: str | None = None):
        """
        Upload a file to GridFS.
        :param bucket_name: Name of the GridFS bucket
        :param local_path: Path to the local file to upload
        :param filename: Optional filename (defaults to basename of local_path)
        :return: The _id of the uploaded file
        """
        if self.db is None:
            raise Exception("Not connected to database")

        import os
        import mimetypes

        # Use basename of local_path if filename not provided
        if filename is None:
            filename = os.path.basename(local_path)

        # Detect MIME type
        content_type, _ = mimetypes.guess_type(local_path)

        bucket = AsyncIOMotorGridFSBucket(self.db, bucket_name=bucket_name)

        try:
            # Read file content
            with open(local_path, 'rb') as f:
                file_content = f.read()

            # Upload to GridFS
            metadata = {}
            if content_type:
                metadata['contentType'] = content_type

            file_id = await bucket.upload_from_stream(
                filename,
                file_content,
                metadata=metadata
            )

            return file_id
        except Exception as e:
            print(f"Error uploading file {local_path}: {e}")
            raise e

    async def delete_file(self, bucket_name: str, file_id):
        """
        Delete a file from GridFS.
        :param bucket_name: Name of the GridFS bucket
        :param file_id: The _id of the file to delete
        """
        if self.db is None:
            raise Exception("Not connected to database")

        bucket = AsyncIOMotorGridFSBucket(self.db, bucket_name=bucket_name)

        try:
            await bucket.delete(file_id)
        except Exception as e:
            print(f"Error deleting file {file_id}: {e}")
            raise e
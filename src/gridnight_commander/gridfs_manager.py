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
import glob
import os

import gridfs
import pymongo

from dotenv import load_dotenv

MONGOTERM_DB = "gnc-test"

load_dotenv()

user = os.getenv("MONGO_ROOT_USER")
passwd = os.getenv("MONGO_ROOT_PASSWORD")
server = os.getenv("MONGO_SERVER")
port = os.getenv("MONGO_PORT")

client = pymongo.MongoClient(
    f"mongodb://{user}:{passwd}@{server}:{port}/")

try:
    import magic
    mime = magic.Magic(mime=True)
    def get_mime_type(filename):
        return mime.from_file(fname)
except ImportError as ie:
    import mimetypes
    def get_mime_type(filename):
        return mimetypes.guess_type(filename)[0]


print("💣 Nuking test database...")
client.drop_database(MONGOTERM_DB)
db = client[MONGOTERM_DB]
#fs = gridfs.GridFS(db)

dune_bucket = gridfs.GridFSBucket(db, bucket_name="Dune")
programming_bucket = gridfs.GridFSBucket(db, bucket_name="Programming")
skills_bucket = gridfs.GridFSBucket(db, bucket_name="Life Skills")

print("↗️ Uploading files...")

for fname in glob.glob("test-data/dune/*"):
    with open(fname, "rb") as file_data:
        content_type = get_mime_type(fname)
        dune_bucket.upload_from_stream(
            os.path.basename(fname), file_data,
            metadata={"contentType": content_type})
        print(f"    📂 {fname}")

for fname in glob.glob("test-data/programming/*"):
    with open(fname, "rb") as file_data:
        content_type = get_mime_type(fname)
        programming_bucket.upload_from_stream(
            os.path.basename(fname), file_data,
            metadata={"contentType": content_type})
        print(f"    📂 {fname}")

for fname in glob.glob("test-data/skills/*"):
    with open(fname, "rb") as file_data:
        content_type = get_mime_type(fname)
        skills_bucket.upload_from_stream(
            os.path.basename(fname), file_data,
            metadata={"contentType": content_type})
        print(f"    📂 {fname}")
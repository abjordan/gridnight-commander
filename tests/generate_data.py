import os
import gridfs
import pymongo
from dotenv import load_dotenv

MONGOTERM_DB = 'mongoterm-test'

load_dotenv()

user = os.getenv('MONGO_ROOT_USER')
passwd = os.getenv('MONGO_ROOT_PASSWORD')

client = pymongo.MongoClient(
    f'mongodb://{user}:{passwd}@localhost:27017/')

client.drop_database(MONGOTERM_DB)
db = client[MONGOTERM_DB]
fs = gridfs.GridFS(db)

# Create a couple of files for GridFS
with open('test-data/python-dbs.txt', 'rb') as infile:
    file_id = fs.put(
        infile, 
        filename='python-dbs.txt',
        content_type='text/plain',
        description='Sample file',
    )
    
with open('test-data/ai-risks.md', 'rb') as infile:
    file_id = fs.put(
        infile, filename='ai-risks.md',
        content_type='text/markdown',
        description='Another sample file'
    )

with open('test-data/brush-your-teeth.txt', 'rb') as infile:
    file_id = fs.put(
        infile, filename='brush-your-teeth.txt',
        content_type='text/plain',
        description='Sample, once more'
    )
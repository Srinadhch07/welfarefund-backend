from pymongo import AsyncMongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB = os.getenv("MONGO_DB")

if not MONGO_DB or not MONGO_URL:
    raise ValueError("Database details are missing")

client = AsyncMongoClient(MONGO_URL, tz_aware=True)
db = client[MONGO_DB]

admin_collection = db["admins"]
tokens_collections = db["tokens"]

async def connect_db():
    try:
        await client.admin.command("ping")
        print("Database connection successful.")
    except Exception as e:
        print(e)

async def close_connection():
    try:
        client.close()
        print("Connection closed.")
    except Exception as e:
        print(e)


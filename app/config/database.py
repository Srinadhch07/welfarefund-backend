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
user_collection = db["users"]
tokens_collections = db["tokens"]
payment_settings_collection = db["payment_settings"]
payments_collection = db["payments"]
withdrawal_request_collection = db["withdrawal_requests"]
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


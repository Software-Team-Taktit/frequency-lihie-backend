from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "merhavim")

client: AsyncIOMotorClient = None
db = None

async def connect_to_mongo():
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        await client.server_info()
        print("✅ Connected to MongoDB!")
    except ConnectionFailure:
        print("❌ MongoDB connection failed.")
        raise
    
async def close_mongo_connection():
    client.close()
    print("🔌 MongoDB connection closed.")
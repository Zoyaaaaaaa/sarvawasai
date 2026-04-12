# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
import os
import logging

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://riddhijlalla:sarvawas123@cluster0.pwktedk.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "sarvawas_ai")

client: AsyncIOMotorClient | None = None
db = None

# -------------------- CONNECT --------------------
async def connect_to_mongo():
    global client, db
    if client is None:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        logging.info(f"Connected to MongoDB: {DB_NAME}")
        await create_indexes()

# -------------------- DISCONNECT --------------------
async def close_mongo_connection():
    global client
    if client:
        client.close()
        client = None
        logging.info("MongoDB connection closed.")

# -------------------- GET DATABASE --------------------
def get_database():
    if db is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return db

async def create_indexes():
    """
    Create all necessary indexes for collections.
    Safely handles sparse indexes to allow multiple null values.
    Idempotent: will drop and recreate conflicting indexes.
    """
    try:
        users = db.users
        indexes = await users.index_information()

        # -------------------- blockchainWallet index --------------------
        if "blockchainWallet_1" in indexes:
            await users.drop_index("blockchainWallet_1")
            logging.info("Dropped existing blockchainWallet_1 index to avoid conflict")

        await users.create_index(
            [("blockchainWallet", ASCENDING)],
            unique=True,
            sparse=True,
            name="blockchainWallet_1"
        )
        logging.info("Created sparse unique index blockchainWallet_1")

        # -------------------- email index --------------------
        if "email_1" in indexes:
            await users.drop_index("email_1")
            logging.info("Dropped existing email_1 index to avoid conflict")

        await users.create_index(
            [("email", ASCENDING)],
            unique=True,
            name="email_1"
        )
        logging.info("Created unique index email_1")

    except Exception as e:
        logging.error(f"Error creating indexes: {e}", exc_info=True)
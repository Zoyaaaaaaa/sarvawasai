# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
import os
import logging

MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URL") or "mongodb://127.0.0.1:27017"
DB_NAME = os.getenv("DB_NAME") or os.getenv("MONGODB_DB_NAME") or "sarvawas_ai"
MONGO_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))

client: AsyncIOMotorClient | None = None
db = None

# -------------------- CONNECT --------------------
async def connect_to_mongo():
    global client, db
    if client is None:
        client = AsyncIOMotorClient(
            MONGO_URI,
            serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
        )
        try:
            # Force a server selection at startup so DNS/network errors surface early.
            await client.admin.command("ping")
            db = client[DB_NAME]
            logging.info(f"Connected to MongoDB: {DB_NAME}")
            await create_indexes()
        except Exception:
            logging.error("MongoDB connection failed.", exc_info=True)
            client.close()
            client = None
            db = None
            raise

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
        raise RuntimeError("Database is unavailable. Check MongoDB URI/network and try again.")
    return db

async def create_indexes():
    """
    Create all necessary indexes for collections.
    Safely handles sparse indexes to allow multiple null values.
    Idempotent: will drop and recreate conflicting indexes.
    """
    if db is None:
        logging.warning("Skipping index creation because database is unavailable.")
        return

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
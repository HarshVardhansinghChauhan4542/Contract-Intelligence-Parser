from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING, ASCENDING
from .config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = Database()

async def connect_to_mongodb() -> bool:
    """
    Connect to MongoDB using the settings from config.
    Returns True if connection is successful, False otherwise.
    """
    try:
        # Close existing connection if any
        if db.client is not None:
            await close_database()
            
        # Create new connection
        db.client = AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000  # 5 second timeout
        )
        
        # Test the connection
        await db.client.admin.command('ping')
        db.database = db.client[settings.database_name]
        
        logger.info("Successfully connected to MongoDB!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        db.client = None
        db.database = None
        return False

async def get_database():
    """
    Get the database instance, establishing a connection if necessary.
    Raises RuntimeError if connection cannot be established.
    """
    if db.database is None:
        if not await connect_to_mongodb():
            raise RuntimeError("Failed to connect to MongoDB")
        await create_indexes()
    return db.database

async def create_indexes():
    """
    Create necessary indexes for the database collections.
    """
    try:
        if db.database is None:
            logger.warning("Cannot create indexes: No database connection")
            return
            
        # Create indexes for the contracts collection
        contracts = db.database.contracts
        
        # Create a unique index on contract_id
        await contracts.create_index("contract_id", unique=True)
        
        # Create indexes for frequently queried fields
        await contracts.create_index([("status", ASCENDING)])
        await contracts.create_index([("uploaded_at", DESCENDING)])
        await contracts.create_index([("score", DESCENDING)])
        
        logger.info("Database indexes created/updated successfully")
        
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
        raise



async def close_database():
    if db.client:
        db.client.close()

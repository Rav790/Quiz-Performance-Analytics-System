"""
config.py - Database Configuration
===================================
Loads environment variables from .env file and creates a MongoDB connection.
Returns the MongoClient and the database object for use by other modules.

Uses python-dotenv to load MONGO_URI and DB_NAME from a .env file.
Default: mongodb://localhost:27017 and database 'quiz_analytics'.
"""

import sys
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Load environment variables from .env file in the project root
load_dotenv()

# Read connection settings from environment (with sensible defaults)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "quiz_analytics")


def get_client():
    """
    Create and return a MongoClient connected to MONGO_URI.
    Uses a 5-second timeout so we fail fast if MongoDB is unreachable.
    """
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client


def get_database():
    """
    Return the database object for our quiz analytics project.
    Also verifies the connection is alive by issuing a ping command.
    """
    client = get_client()
    try:
        # The ping command forces a round-trip to verify the server is reachable
        client.admin.command("ping")
        print(f"[OK] Connected to MongoDB at {MONGO_URI}")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"[ERROR] Cannot connect to MongoDB at {MONGO_URI}")
        print(f"  Reason: {e}")
        print()
        print("=== Troubleshooting (Windows) ===")
        print("1. Install MongoDB Community Edition:")
        print("   https://www.mongodb.com/try/download/community")
        print("   Download the MSI installer, run it, and choose 'Complete' setup.")
        print("2. Start the MongoDB service:")
        print('   net start MongoDB')
        print("   Or run mongod manually:")
        print('   "C:\\Program Files\\MongoDB\\Server\\7.0\\bin\\mongod.exe"')
        print("3. Alternatively, use MongoDB Atlas (free tier):")
        print("   - Go to https://cloud.mongodb.com and create a free cluster")
        print("   - Get your connection string and put it in .env as MONGO_URI")
        print("   - Format: mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority")
        sys.exit(1)

    db = client[DB_NAME]
    return db


def check_replica_set(client):
    """
    Check if the MongoDB deployment is a replica set (needed for transactions).
    Returns True if replica set, False otherwise.
    
    mongosh equivalent:
        rs.status()
    """
    try:
        result = client.admin.command("replSetGetStatus")
        return True
    except Exception:
        # Standalone deployments throw an error for replSetGetStatus
        return False


if __name__ == "__main__":
    # Quick connectivity test
    db = get_database()
    print(f"[OK] Database: {db.name}")
    print(f"[OK] Collections: {db.list_collection_names()}")
    client = db.client
    print(f"[OK] Replica set: {check_replica_set(client)}")

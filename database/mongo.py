# database/mongo.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv
from flask import g

load_dotenv()

class MongoDBConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
            cls._instance._client = None
            cls._instance._db = None
            cls._instance._initialized = False
        return cls._instance
    
    def init_app(self, app):
        """Initialize MongoDB with Flask app"""
        self._initialized = True
        

    
    def connect(self):
        """Connect to MongoDB Atlas"""
        try:
            if self._client is not None and self._db is not None:
                return self._db
            
            MONGO_URI = os.getenv("MONGO_URI")
            
            if not MONGO_URI:
                raise ValueError("MONGO_URI environment variable is not set")
            
            print(f"🔗 Connecting to MongoDB Atlas...")
            
            # Connection options for MongoDB Atlas
            self._client = MongoClient(
                MONGO_URI,
                maxPoolSize=50,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                retryWrites=True,
                retryReads=True,
                serverSelectionTimeoutMS=5000
            )
            
            # Test the connection
            self._client.admin.command('ping')
            
            DB_NAME = os.getenv("DB_NAME", "dastawez")
            self._db = self._client[DB_NAME]
            
            print(f"✅ MongoDB Atlas connected successfully! Database: {DB_NAME}")
            return self._db
            
        except ConnectionFailure as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise
        except Exception as e:
            print(f"❌ Error connecting to MongoDB: {e}")
            raise
    
    def get_db(self):
        """Get database instance"""
        if self._client is None or self._db is None:
            return self.connect()
        return self._db
    
    def get_client(self):
        """Get MongoDB client"""
        if self._client is None:
            self.connect()
        return self._client
    
    def close(self):
        """Close the connection"""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            print("📴 MongoDB connection closed")
    
    @property
    def client(self):
        return self._client
    
    @property
    def db(self):
        return self._db

# Create singleton instance
db_connection = MongoDBConnection()
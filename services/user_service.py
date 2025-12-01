# services/user_service.py
from database.mongo import db_connection
from models.user_model import User
from datetime import datetime
import traceback
from bson import ObjectId

def get_collection():
    """Get users collection with fresh db connection"""
    db = db_connection.get_db()
    return db['users']

def save_user_data(user_data, tokens=None):
    """Insert or update user in MongoDB"""
    try:
        print(f"🔄 Saving user data for: {user_data.get('email')}")
        
        email = user_data.get("email")
        
        if not email:
            print("❌ No email provided")
            return False
            
        users_collection = get_collection()
        
        # Check if user exists
        existing = users_collection.find_one({"email": email})
        
        # Prepare user document
        user_doc = {
            "google_id": user_data.get("id"),
            "name": user_data["name"],
            "email": email,
            "picture": user_data.get("picture"),
            "last_login": datetime.utcnow(),
            "access_token": tokens.get("access_token") if tokens else None,
            "refresh_token": tokens.get("refresh_token") if tokens else None
        }
        
        if existing:
            # Update existing user
            result = users_collection.update_one(
                {"email": email},
                {"$set": user_doc}
            )
            print(f"✅ Updated existing user: {email}, modified: {result.modified_count}")
        else:
            # Insert new user
            user_doc['created_at'] = datetime.utcnow()
            result = users_collection.insert_one(user_doc)
            print(f"✅ Inserted new user: {email}, id: {result.inserted_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in save_user_data: {str(e)}")
        traceback.print_exc()
        return False

def get_user_by_email(email):
    """Get user by email from MongoDB"""
    try:
        users_collection = get_collection()
        user_data = users_collection.find_one({"email": email})
        if user_data:
            user = User.from_dict(user_data)
            print(f"✅ Found user: {email}")
            return user
        else:
            print(f"⚠️ User not found: {email}")
            return None
    except Exception as e:
        print(f"❌ Error in get_user_by_email: {str(e)}")
        return None

def get_user_by_id(user_id):
    """Get user by ObjectId"""
    try:
        if not ObjectId.is_valid(user_id):
            print(f"❌ Invalid ObjectId: {user_id}")
            return None
        
        users_collection = get_collection()
        user_data = users_collection.find_one({"_id": ObjectId(user_id)})
        if user_data:
            user = User.from_dict(user_data)
            print(f"✅ Found user by ID: {user_id}")
            return user
        else:
            print(f"⚠️ User not found by ID: {user_id}")
            return None
    except Exception as e:
        print(f"❌ Error in get_user_by_id: {str(e)}")
        return None

def get_all_users():
    """Get all users from MongoDB"""
    try:
        users_collection = get_collection()
        users_data = list(users_collection.find().sort("created_at", -1))
        users = [User.from_dict(user_data) for user_data in users_data]
        print(f"✅ Found {len(users)} users")
        return users
    except Exception as e:
        print(f"❌ Error in get_all_users: {str(e)}")
        return []

def update_user(email, update_data):
    """Update user by email"""
    try:
        users_collection = get_collection()
        # Add updated_at timestamp
        update_data['updated_at'] = datetime.utcnow()
        
        result = users_collection.update_one(
            {"email": email},
            {"$set": update_data}
        )
        print(f"✅ Updated user {email}: {result.modified_count} modified")
        return result.modified_count > 0
    except Exception as e:
        print(f"❌ Error in update_user: {str(e)}")
        return False

def delete_user(email):
    """Delete user by email"""
    try:
        users_collection = get_collection()
        result = users_collection.delete_one({"email": email})
        print(f"✅ Deleted user {email}: {result.deleted_count} deleted")
        return result.deleted_count > 0
    except Exception as e:
        print(f"❌ Error in delete_user: {str(e)}")
        return False

def count_users():
    """Count total users"""
    try:
        users_collection = get_collection()
        count = users_collection.count_documents({})
        return count
    except Exception as e:
        print(f"❌ Error in count_users: {str(e)}")
        return 0

def create_indexes():
    """Create indexes for better performance"""
    try:
        users_collection = get_collection()
        # Create unique index on email
        users_collection.create_index([("email", 1)], unique=True)
        
        # Create index on google_id
        users_collection.create_index([("google_id", 1)])
        
        # Create index on last_login for sorting
        users_collection.create_index([("last_login", -1)])
        
        print("✅ Database indexes created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        return False
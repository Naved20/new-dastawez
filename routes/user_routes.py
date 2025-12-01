# routes/user_routes.py
from flask import Blueprint, request, jsonify
from services.user_service import (
    save_user_data,
    get_user_by_email,
    get_user_by_id,
    get_all_users,
    delete_user,
    update_user,
    count_users
)
from models.user_model import User
from bson import ObjectId

user_routes = Blueprint("user_routes", __name__)

@user_routes.route("/users", methods=["POST"])
def route_create_user():
    """Create a new user"""
    data = request.json

    if not data.get("email"):
        return jsonify({"error": "Email is required"}), 400

    success = save_user_data(data)
    if success:
        return jsonify({"message": "User created successfully"}), 201
    else:
        return jsonify({"error": "Failed to create user"}), 500

@user_routes.route("/users", methods=["GET"])
def route_get_all_users():
    """Get all users"""
    users = get_all_users()
    # Convert User objects to dictionaries
    users_list = [user.to_dict() for user in users]
    return jsonify(users_list), 200

@user_routes.route("/users/<identifier>", methods=["GET"])
def route_get_user(identifier):
    """Get user by email or ID"""
    # Check if identifier is an email
    if '@' in identifier:
        user = get_user_by_email(identifier)
    else:
        # Try as ObjectId
        user = get_user_by_id(identifier)
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict()), 200

@user_routes.route("/users/<email>", methods=["PUT"])
def route_update_user(email):
    """Update user by email"""
    data = request.json
    
    # Remove any protected fields
    data.pop('_id', None)
    data.pop('created_at', None)
    
    success = update_user(email, data)
    if success:
        return jsonify({"message": "User updated successfully"}), 200
    else:
        return jsonify({"error": "Failed to update user"}), 500

@user_routes.route("/users/<email>", methods=["DELETE"])
def route_delete_user(email):
    """Delete user by email"""
    success = delete_user(email)
    if success:
        return jsonify({"message": "User deleted successfully"}), 200
    else:
        return jsonify({"error": "Failed to delete user"}), 500

@user_routes.route("/users/count", methods=["GET"])
def route_count_users():
    """Count total users"""
    count = count_users()
    return jsonify({"count": count}), 200

@user_routes.route("/users/search", methods=["GET"])
def route_search_users():
    """Search users by name or email"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    
    try:
        from database.mongo import db
        users_collection = db['users']
        
        # Create search query (case-insensitive)
        search_query = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}}
            ]
        }
        
        users_data = list(users_collection.find(search_query).limit(20))
        users = [User.from_dict(user_data).to_dict() for user_data in users_data]
        
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
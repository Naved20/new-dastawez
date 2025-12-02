# models/session_model.py
from datetime import datetime, timedelta
from database.mongo import db_connection
import secrets
from flask import request

def get_sessions_collection():
    db = db_connection.get_db()
    return db['sessions']

class UserSession:
    def __init__(self, user_email, session_id=None, created_at=None, expires_at=None):
        self.session_id = session_id or secrets.token_urlsafe(32)
        self.user_email = user_email
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at or (datetime.utcnow() + timedelta(days=30))
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'user_email': self.user_email,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr
        }
    
    def save(self):
        sessions_collection = get_sessions_collection()
        sessions_collection.update_one(
            {'session_id': self.session_id},
            {'$set': self.to_dict()},
            upsert=True
        )
    
    @staticmethod
    def get_by_id(session_id):
        sessions_collection = get_sessions_collection()
        data = sessions_collection.find_one({'session_id': session_id})
        if data and data['expires_at'] > datetime.utcnow():
            return UserSession(
                session_id=data['session_id'],
                user_email=data['user_email'],
                created_at=data['created_at'],
                expires_at=data['expires_at']
            )
        return None
    
    @staticmethod
    def delete(session_id):
        sessions_collection = get_sessions_collection()
        sessions_collection.delete_one({'session_id': session_id})
    
    @staticmethod
    def delete_all_for_user(user_email):
        sessions_collection = get_sessions_collection()
        sessions_collection.delete_many({'user_email': user_email})
    
    def is_valid(self):
        return self.expires_at > datetime.utcnow()
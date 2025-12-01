# models/user_model.py
from datetime import datetime
from bson import ObjectId

class User:
    def __init__(
        self,
        google_id=None,
        name=None,
        email=None,
        picture=None,
        access_token=None,
        refresh_token=None,
        created_at=None,
        last_login=None,
        _id=None
    ):
        self._id = _id if _id else ObjectId()
        self.google_id = google_id
        self.name = name
        self.email = email
        self.picture = picture
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.created_at = created_at or datetime.utcnow()
        self.last_login = last_login or datetime.utcnow()
    
    def to_dict(self):
        """Convert User object to dictionary"""
        user_dict = {
            "google_id": self.google_id,
            "name": self.name,
            "email": self.email,
            "picture": self.picture,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "created_at": self.created_at,
            "last_login": self.last_login
        }
        
        if hasattr(self, '_id') and self._id:
            user_dict['_id'] = self._id
        
        return user_dict
    
    @classmethod
    def from_dict(cls, data):
        """Create User object from dictionary"""
        if not data:
            return None
        
        return cls(
            _id=data.get('_id'),
            google_id=data.get('google_id'),
            name=data.get('name'),
            email=data.get('email'),
            picture=data.get('picture'),
            access_token=data.get('access_token'),
            refresh_token=data.get('refresh_token'),
            created_at=data.get('created_at'),
            last_login=data.get('last_login')
        )
    
    @property
    def id(self):
        """Get string representation of ObjectId"""
        return str(self._id) if self._id else None
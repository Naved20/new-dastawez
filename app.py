# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from authlib.integrations.flask_client import OAuth
import os
from functools import wraps
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize MongoDB connection - don't import db directly yet
from database.mongo import db_connection

# Import routes
from routes.user_routes import user_routes

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'b3f7ac0694f59e4983adb080c3f4ca48621b0b0ce1759d07422cabf6b5bd7ea4')

# Initialize MongoDB with app
db_connection.init_app(app)

# Session Configuration
app.config.update(
    SESSION_COOKIE_SECURE=False if not os.getenv('VERCEL') else True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600,
    SESSION_COOKIE_DOMAIN=None,
    SESSION_REFRESH_EACH_REQUEST=True,
    # Add MongoDB URI to config
    MONGO_URI=os.getenv("MONGO_URI"),
    DB_NAME=os.getenv("DB_NAME", "dastawez")
)

# Register blueprints
# app.register_blueprint(user_routes, url_prefix='/api') # Temporarily commented out for debugging

# OAuth Configuration
oauth = OAuth(app)

# Determine redirect URI based on environment
if os.getenv('VERCEL'):
    REDIRECT_URI = 'https://new-dastawez.vercel.app/auth/callback'
else:
    REDIRECT_URI = 'http://127.0.0.1:5000/auth/callback'

print(f"🔧 Using Redirect URI: {REDIRECT_URI}")

# Register Google OAuth
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'redirect_uri': REDIRECT_URI
    }
)

# Initialize database connection
def get_users_collection():
    """Get users collection with fresh connection"""
    db = db_connection.get_db()
    return db['users']

# Import and initialize indexes AFTER db is ready
def initialize_database():
    """Initialize database indexes"""
    try:
        from services.user_service import create_indexes
        create_indexes()
        print("✅ Database indexes created successfully")
    except Exception as e:
        print(f"⚠️ Could not create indexes: {e}")

# Call initialization
initialize_database()

# Decorator for protected routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please login first!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    user = session.get('user')
    return render_template('index.html', user=user)

@app.route('/login')
def login():
    try:
        print(f"🔗 Using redirect URI: {REDIRECT_URI}")
        return google.authorize_redirect(REDIRECT_URI)
    except Exception as e:
        flash('Login service is temporarily unavailable.', 'error')
        print(f"❌ Login error: {e}")
        return redirect(url_for('index'))

@app.route('/auth/callback')
def auth_callback():
    try:
        print("🔄 OAuth callback started...")
        token = google.authorize_access_token()
        user_info = google.userinfo()
        
        if user_info:
            print(f"✅ User info received: {user_info.get('email')}")
            user_data = {
                'id': user_info.get('sub'),
                'name': user_info.get('name'),
                'email': user_info.get('email'),
                'picture': user_info.get('picture')
            }
            
            print(f"📋 Saving user data: {user_data}")
            
            from services.user_service import save_user_data
            save_success = save_user_data(user_data, {
                'access_token': token.get('access_token'),
                'refresh_token': token.get('refresh_token')
            })
            
            print(f"💾 Save result: {save_success}")
            
            if save_success:
                session.clear()
                session['user'] = {
                    'name': user_info.get('name'),
                    'email': user_info.get('email'),
                    'picture': user_info.get('picture')
                }
                session.permanent = True 
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Login successful but data save failed.', 'warning')
                return redirect(url_for('index'))
        else:
            flash('Login failed. Please try again.', 'error')
            
    except Exception as e:
        flash('Login error. Please try again.', 'error')
        print(f"❌ Auth callback error: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
# @login_required # Temporarily commented out for debugging
def dashboard():
    user = session.get('user')
    if user:
        from services.user_service import get_user_by_email
        db_user = get_user_by_email(user['email'])
        print(f"📊 Dashboard accessed by: {user['email']}, DB user: {db_user is not None}")
        
        # Add current date to template
        return render_template(
            'dashboard.html', 
            user=user, 
            db_user=db_user,
            now=datetime.now()  # Add current datetime
        )
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_users():
    from services.user_service import get_all_users
    users = get_all_users()
    return render_template('admin_users.html', users=users, current_user=session.get('user'))

# Debug routes
@app.route('/debug')
def debug():
    return {
        'vercel_env': os.getenv('VERCEL'),
        'vercel_url': os.getenv('VERCEL_URL'),
        'redirect_uri': REDIRECT_URI,
        'session_user': session.get('user'),
        'python_version': os.sys.version,
        'mongo_connected': db_connection.client is not None
    }

@app.route('/debug/db')
def debug_db():
    """Debug database connection"""
    try:
        users_collection = get_users_collection()
        users_count = users_collection.count_documents({})
        users = list(users_collection.find({}, {'_id': 0, 'name': 1, 'email': 1}).limit(5))
        
        return {
            'status': 'connected',
            'database': db_connection.db.name if db_connection.db else None,
            'collection': 'users',
            'total_users': users_count,
            'sample_users': users,
            'connection_alive': db_connection.client is not None
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

@app.route('/debug/save-test')
def debug_save_test():
    """Test user save functionality"""
    from services.user_service import save_user_data
    
    test_user = {
        "id": "debug_123",
        "name": "Debug User",
        "email": "debug@example.com",
        "picture": "debug.jpg"
    }
    
    success = save_user_data(test_user, {
        "access_token": "debug_token",
        "refresh_token": "debug_refresh"
    })
    
    return {
        "success": success,
        "user": test_user,
        "collection": "users",
        "connection_alive": db_connection.client is not None
    }

@app.route('/debug/ping')
def debug_ping():
    """Ping MongoDB to check connection"""
    try:
        # Ping the database
        db_connection.client.admin.command('ping')
        return {
            "status": "connected",
            "message": "MongoDB connection is active",
            "database": db_connection.db.name if db_connection.db else None
        }
    except Exception as e:
        return {
            "status": "disconnected",
            "error": str(e)
        }



@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=session.get('user'))

@app.route('/orders')
@login_required
def orders():
    return render_template('orders.html', user=session.get('user'))

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=session.get('user'))

@app.route('/edit_profile')
@login_required
def edit_profile():
    return render_template('edit_profile.html', user=session.get('user'))

# Add similar routes for services
@app.route('/document_creation')
@login_required
def document_creation():
    return render_template('document_creation.html', user=session.get('user'))


# Add similar routes for services
@app.route('/affidavit_creation')
@login_required
def affidavit_creation():
    return render_template('document_creation.html', user=session.get('user'))


# Add similar routes for services
@app.route('/document_printing')
@login_required
def document_printing():
    return render_template('document_printing.html', user=session.get('user'))




if __name__ == '__main__':
    # Ensure MongoDB is connected before starting
    print("🚀 Starting Flask application...")
    
    # Connect to MongoDB
    db = db_connection.get_db()
    print(f"📊 Database: {db.name}")
    print(f"🔗 Connection status: {'Connected' if db_connection.client is not None else 'Disconnected'}")
    
    print("\n📝 Registered URL Rules:")
    for rule in app.url_map.iter_rules():
        print(f"  Endpoint: {rule.endpoint}, Methods: {rule.methods}, Rule: {rule.rule}")
    print("--- End URL Rules ---\n")

    app.run(debug=True, host='0.0.0.0', port=5000)

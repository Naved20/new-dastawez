from flask import Flask, render_template, request, redirect, url_for, session, flash
from authlib.integrations.flask_client import OAuth
import os
import sqlite3
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'b3f7ac0694f59e4983adb080c3f4ca48621b0b0ce1759d07422cabf6b5bd7ea4')

# Session Configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600,
    SESSION_COOKIE_DOMAIN=None,  # Let Flask handle domain
    SESSION_REFRESH_EACH_REQUEST=True
)

# OAuth Configuration
oauth = OAuth(app)

# ✅ EXACT REDIRECT URIS USE KAREN
if os.getenv('VERCEL'):
    REDIRECT_URI = 'https://new-dastawez.vercel.app/auth/callback'
else:
    REDIRECT_URI = 'http://127.0.0.1:5000/auth/callback'

print(f"🔧 Using Redirect URI: {REDIRECT_URI}")

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


# Database Configuration (aapka existing code)
DATABASE_NAME = 'dastawez.db'
def init_database():
    """Initialize SQLite database and create tables"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oauth_callbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                google_id TEXT UNIQUE,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                picture TEXT,
                access_token TEXT,
                refresh_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def save_user_data(user_data, tokens=None):
    """Save or update user data in database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM oauth_callbacks WHERE email = ?', (user_data['email'],))
        existing_user = cursor.fetchone()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if existing_user:
            cursor.execute('''
                UPDATE oauth_callbacks 
                SET name = ?, picture = ?, last_login = ?, access_token = ?, refresh_token = ?
                WHERE email = ?
            ''', (
                user_data['name'], 
                user_data['picture'], 
                current_time, 
                tokens.get('access_token') if tokens else None,
                tokens.get('refresh_token') if tokens else None,
                user_data['email']
            ))
            print(f"✅ User updated: {user_data['email']}")
        else:
            cursor.execute('''
                INSERT INTO oauth_callbacks 
                (google_id, name, email, picture, access_token, refresh_token, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data.get('id'),
                user_data['name'],
                user_data['email'],
                user_data['picture'],
                tokens.get('access_token') if tokens else None,
                tokens.get('refresh_token') if tokens else None,
                current_time,
                current_time
            ))
            print(f"✅ New user saved: {user_data['email']}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error saving user data: {e}")
        return False

def get_user_by_email(email):
    """Get user data by email"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM oauth_callbacks WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        print(f"❌ Error getting user data: {e}")
        return None

def get_all_users():
    """Get all users from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM oauth_callbacks ORDER BY created_at DESC')
        users = cursor.fetchall()
        conn.close()
        return users
    except Exception as e:
        print(f"❌ Error getting all users: {e}")
        return []

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please login first!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    user = session.get('user')
    return render_template('index.html', user=user)

@app.route('/login')
def login():
    try:
        print(f"🔗 Using redirect URI: {REDIRECT_URI}")
        return google.authorize_redirect(REDIRECT_URI)  # ✅ DIRECT URI USE KAREN
    except Exception as e:
        flash('Login service is temporarily unavailable.', 'error')
        print(f"❌ Login error: {e}")
        return redirect(url_for('dashboard'))

@app.route('/auth/callback')
def auth_callback():
    try:
        
        token = google.authorize_access_token()
        user_info = google.userinfo()
        
        if user_info:
            user_data = {
                'id': user_info.get('sub'),
                'name': user_info.get('name'),
                'email': user_info.get('email'),
                'picture': user_info.get('picture')
            }
            
            save_success = save_user_data(user_data, {
                'access_token': token.get('access_token'),
                'refresh_token': token.get('refresh_token')
            })
            
            if save_success:

                session.clear()
                session['user'] = {
                    'name': user_info.get('name'),
                    'email': user_info.get('email'),
                    'picture': user_info.get('picture')
                }
                session.permanent = True 
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))  # ✅ DASHBOARD PE redirect
            else:
                flash('Login successful but data save failed.', 'warning')
        else:
            flash('Login failed. Please try again.', 'error')
            
    except Exception as e:
        flash('Login error. Please try again.', 'error')
        import traceback
        traceback.print_exc()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = session.get('user')
    db_user = get_user_by_email(user['email']) if user else None
    return render_template('dashboard.html', user=user, db_user=db_user)

@app.route('/admin')
@login_required
def admin_users():
    users = get_all_users()
    return render_template('admin_users.html', users=users, current_user=session.get('user'))

# ✅ DEBUG ROUTE ADD KAREN
@app.route('/debug')
def debug():
    return {
        'vercel_env': os.getenv('VERCEL'),
        'vercel_url': os.getenv('VERCEL_URL'),
        'redirect_uri': REDIRECT_URI,
        'session_user': session.get('user')
    }

# Initialize database when app starts
with app.app_context():
    init_database()

if __name__ == '__main__':
    app.run(debug=True)
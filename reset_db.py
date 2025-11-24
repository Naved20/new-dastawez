import sqlite3
import os

def reset_sqlite_db(db_path):
    """Completely reset SQLite database by deleting and recreating it"""
    try:
        # Close any existing connections
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Database {db_path} deleted")
        
        # Create new database
        conn = sqlite3.connect(db_path)
        conn.close()
        print(f"New database {db_path} created")
        
    except Exception as e:
        print(f"Error resetting database: {e}")

# Usage
reset_sqlite_db('dastawez.db')
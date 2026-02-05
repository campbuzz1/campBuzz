import sqlite3
import hashlib

def init_db():
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    
    # 1. Table for Events (Updated with 'organizer')
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            organizer TEXT DEFAULT 'Unknown', -- New Column for Telegram Username
            status TEXT DEFAULT 'pending'
        )
    ''')

    # 2. Table for Admin Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # 3. Create Default Admin
    default_user = "admin"
    default_pass = "password123"
    hashed_pass = hashlib.sha256(default_pass.encode()).hexdigest()

    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (default_user, hashed_pass))
        print(f"✅ Admin created: {default_user} / {default_pass}")
    except sqlite3.IntegrityError:
        print("ℹ️ Admin user already exists.")

    conn.commit()
    conn.close()
    print("✅ Database ready with new schema.")

if __name__ == '__main__':
    init_db()
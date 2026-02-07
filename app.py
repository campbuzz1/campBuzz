from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, flash
import sqlite3
import hashlib
from datetime import datetime, timedelta
from functools import wraps
import os
from dotenv import load_dotenv  # <--- Import this
from flask_wtf.csrf import CSRFProtect
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
csrf = CSRFProtect(app) # This protects every POST route automatically



# --- DATABASE CONNECTION ---
def get_db_connection():
    conn = sqlite3.connect('events.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- UTILS ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Please login to access the Admin Panel.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ---

@app.route('/')
def home():
    conn = get_db_connection()
    # Fetch only Approved events, sorted by nearest date first
    events = conn.execute('SELECT * FROM events WHERE status = "approved" ORDER BY date ASC').fetchall()
    conn.close()
    
    # Render the new HTML file from the 'templates' folder
    return render_template('index.html', events=events)

# --- ADMIN ROUTES (Using Simple Internal Templates) ---
# We keep the Admin Panel simple for now, separate from the fancy user UI

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CampBuzz Admin</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Poppins:wght@400;600;800&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary: #ff4757;
            --dark-blue: #2f3542;
            --text-gray: #57606f;
            --bg-color: #f1f2f6;
            --white: #ffffff;
            --shadow: 0 4px 15px rgba(0,0,0,0.08);
            --success: #2ed573;
            --warning: #ffa502;
        }
        body { 
            font-family: 'Poppins', sans-serif; 
            background-color: var(--bg-color); 
            margin: 0; padding: 20px; 
            color: var(--dark-blue);
        }
        .container { max-width: 900px; margin: 0 auto; padding-bottom: 50px; }

        header { 
            text-align: center; 
            margin-bottom: 50px; 
        }
        
        /* Logo Styles */
        .logo-container {
            margin-bottom: 10px;
        }

        .logo { 
            font-family: 'DM Serif Display', serif; 
            font-size: 3.5rem; 
            font-weight: 400; 
            color: var(--dark-blue); 
            text-decoration: none; 
            line-height: 1;
        }
        
        .logo span { 
            color: var(--primary); 
        }
        
        /* Tagline Styles */
        .tagline {
            font-family: 'DM Serif Display', serif;
            font-size: 1.2rem;
            color: var(--text-gray);
            font-style: normal; 
            margin-top: 5px;
            opacity: 0.8;
        }
        
        nav { margin-top: 25px; font-size: 0.9rem; }
        nav a { color: var(--text-gray); text-decoration: none; margin: 0 10px; font-weight: 600; }

        .card { 
            background: var(--white); 
            padding: 20px; 
            margin-bottom: 20px; 
            border-radius: 20px; 
            box-shadow: var(--shadow);
            border: none;
            position: relative;
            overflow: hidden;
        }
        
        /* Empty State Styles */
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            background: transparent;
            box-shadow: none;
        }
        .empty-state h3 {
            font-family: 'DM Serif Display', serif;
            font-size: 1.5rem;
            color: var(--text-gray);
            margin-bottom: 10px;
            font-weight: 400;
        }
        .empty-state p {
            font-family: 'Poppins', sans-serif;
            color: var(--text-gray);
            opacity: 0.7;
        }

        .status-badge {
            position: absolute;
            top: 0; right: 0;
            padding: 5px 15px;
            font-size: 0.7rem;
            font-weight: 800;
            text-transform: uppercase;
            border-bottom-left-radius: 15px;
            color: white;
        }
        .pending-bg { background: var(--warning); }
        .approved-bg { background: var(--success); }

        h2 { font-size: 1.2rem; margin-top: 0; color: var(--dark-blue); }
        p { color: var(--text-gray); font-size: 0.9rem; margin: 5px 0; }
        .flash { 
            background: #ffeaa7; padding: 12px; border-radius: 10px; 
            margin-bottom: 20px; font-size: 0.85rem; text-align: center; 
            color: #d63031; font-weight: 600;
        }

        label { display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 5px; color: var(--text-gray); }
        input, textarea { 
            width: 100%; padding: 12px; margin-bottom: 15px; 
            border-radius: 10px; border: 1px solid #ddd; 
            box-sizing: border-box; font-family: inherit;
        }
        .btn { 
            padding: 10px 18px; border-radius: 10px; border: none; 
            font-weight: 600; cursor: pointer; font-size: 0.85rem;
            transition: opacity 0.2s; display: inline-block; text-decoration: none;
        }
        .btn:hover { opacity: 0.8; }
        .btn-primary { background: var(--primary); color: white; }
        .btn-success { background: var(--success); color: white; }
        .btn-outline { background: transparent; border: 1px solid #ddd; color: var(--text-gray); }
        .btn-danger { background: #ff7675; color: white; }
        .btn-block { width: 100%; padding: 14px; }

        .actions { display: flex; gap: 10px; margin-top: 15px; align-items: center; }
        .delete-form { margin-left: auto; }
    </style>
</head>
<body>
    {% if page not in ['login', 'edit', 'dashboard'] %}
    {% set page = 'dashboard' %}
    {% endif %}

    <div class="container">
        <header>
            <div class="logo-container">
                <a href="/" class="logo">Camp<span>Buzz</span></a>
                <div class="tagline">Never miss a Buzz</div>
            </div>
            
            <nav>
                {% if session.get('logged_in') %}
                    <a href="/admin">Dashboard</a>
                    <a href="/logout" style="color: var(--primary);">Logout</a>
                {% else %}
                    <a href="/">← Back Home</a>
                {% endif %}
            </nav>
        </header>

        {% with messages = get_flashed_messages() %}
        {% if messages %}
            <div class="card">
                <div class="flash">{{ messages[0] | replace('Please login to access the Admin Panel.', 'Please login to proceed') }}</div>
            </div>
        {% endif %}
        {% endwith %}


        {% if page == 'login' %}
            <div class="card">
                <h2 style="text-align: center;">Login</h2>
                <form method="post">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <label>Username</label>
                    <input type="text" name="username" placeholder="Enter username" required>
                    <label>Password</label>
                    <input type="password" name="password" placeholder="Enter password" required>
                    <button class="btn btn-primary btn-block">Sign In</button>
                </form>
            </div>

        {% elif page == 'edit' %}
            <div class="card">
                <h2>✏️ Edit Event</h2>
                <form method="post">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <label>Event Title</label>
                    <input type="text" name="title" value="{{ event['title'] }}" required>
                    
                    <label>Date (YYYY-MM-DD)</label>
                    <input type="text" name="date" value="{{ event['date'] }}" required>
                    
                    <label>Description</label>
                    <textarea name="description" rows="5" required>{{ event['description'] }}</textarea>
                    
                    <div class="actions">
                        <button type="submit" class="btn btn-primary">Save Changes</button>
                        <a href="/admin" class="btn btn-outline">Cancel</a>
                    </div>
                </form>
            </div>

        {% else %}
            {% if events %}
                <h2 style="margin-bottom: 20px;">Event Queue</h2>
            {% endif %}
            
            {% for event in events %}
                <div class="card">
                    <div class="status-badge {% if event['status']=='pending' %}pending-bg{% else %}approved-bg{% endif %}">
                        {{ event['status'] }}
                    </div>
                    <h2>{{ event['title'] }}</h2>
                    <p>📅 <b>Date:</b> {{ event['date'] }}</p>
                    <p>👤 <b>By:</b> {{ event['organizer'] }}</p>
                    <p style="margin-top: 10px;">{{ event['description'] }}</p>
                    
                    <div class="actions">
                        {% if event['status'] == 'pending' %}
                        <form action="/approve/{{ event['id'] }}" method="post">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                            <button class="btn btn-success">Approve</button>
                        </form>
                        {% endif %}
                        
                        <a href="/edit/{{ event['id'] }}" class="btn btn-outline">Edit</a>
                        
                        <form action="/delete/{{ event['id'] }}" method="post" class="delete-form">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                            <button class="btn btn-danger" onclick="return confirm('Delete this event?')">🗑️</button>
                        </form>
                    </div>
                </div>
            {% else %}
                <div class="card empty-state">
                    <h3>No Buzz Yet 🐝</h3>
                    <p>Wait for the Admin to post updates!</p>
                </div>
            {% endfor %}
        {% endif %}
    </div>
</body>
</html>
"""
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Load credentials from .env
        env_user = os.getenv('ADMIN_USER')
        env_pass = os.getenv('ADMIN_PASS')
        
        # Check against Environment Variables
        if username == env_user and password == env_pass:
            session['logged_in'] = True
            flash("Welcome back, Admin!", "success")
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid username or password!', 'error')
            # If login fails, we MUST return the template again
            return render_template_string(ADMIN_TEMPLATE, page='login', events=[])
    
    # This covers the 'GET' request (initial page load)
    return render_template_string(ADMIN_TEMPLATE, page='login', events=[])

@app.route('/admin')
@login_required
def admin_panel():
    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events ORDER BY status DESC, date ASC').fetchall()
    conn.close()
    return render_template_string(ADMIN_TEMPLATE, page='dashboard', events=events)

@app.route('/approve/<int:event_id>', methods=['POST'])
@login_required
def approve_event(event_id):
    conn = get_db_connection()
    conn.execute('UPDATE events SET status = "approved" WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- EDIT FEATURE (Simplified for brevity) ---
# --- REAL EDIT FUNCTION ---
@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    conn = get_db_connection()
    
    # 1. HANDLE SAVING (POST Request)
    if request.method == 'POST':
        title = request.form['title']
        date_input = request.form['date']
        desc = request.form['description']

        # Validate Date Format (Important so Auto-Delete doesn't break)
        try:
            datetime.strptime(date_input, '%Y-%m-%d')
        except ValueError:
            flash("⚠️ Error: Date must be YYYY-MM-DD (e.g., 2026-02-25)")
            # Reload form with bad data so user can fix it
            event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
            conn.close()
            return render_template_string(ADMIN_TEMPLATE, page='edit', event=event)

        # Update Database
        conn.execute('UPDATE events SET title = ?, date = ?, description = ? WHERE id = ?', 
                     (title, date_input, desc, event_id))
        conn.commit()
        conn.close()
        
        flash("✅ Event updated successfully!")
        return redirect(url_for('admin_panel'))

    # 2. HANDLE SHOWING FORM (GET Request)
    else:
        event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
        conn.close()
        
        if not event:
            flash("Event not found.")
            return redirect(url_for('admin_panel'))
            
        # Show the 'edit' page mode
        return render_template_string(ADMIN_TEMPLATE, page='edit', event=event)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
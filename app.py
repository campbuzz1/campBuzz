from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
import hashlib
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this'

def get_db_connection():
    conn = sqlite3.connect('events.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- SECURITY ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Please login first.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def cleanup_old_events():
    conn = get_db_connection()
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    conn.execute('DELETE FROM events WHERE date < ?', (yesterday,))
    conn.commit()
    conn.close()

# --- HTML TEMPLATE (Enhanced with Edit Mode) ---
HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Event Notifier</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; max-width: 900px; margin: auto; background: #f8f9fa; }
        .flash { padding: 15px; background: #ffeeba; border-left: 5px solid #ffc107; margin-bottom: 20px; border-radius: 4px;}
        .flash.success { background: #d4edda; border-left-color: #28a745; }
        .flash.error { background: #f8d7da; border-left-color: #dc3545; }
        
        .card { background: white; border: 1px solid #e0e0e0; padding: 25px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .badge { background: #eee; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; color: #555; }
        
        .btn { padding: 8px 16px; cursor: pointer; text-decoration: none; border-radius: 5px; border: none; font-size: 14px; font-weight: 600; transition: background 0.2s; }
        .btn-green { background-color: #28a745; color: white; }
        .btn-green:hover { background-color: #218838; }
        .btn-red { background-color: #dc3545; color: white; }
        .btn-red:hover { background-color: #c82333; }
        .btn-blue { background-color: #007bff; color: white; }
        .btn-grey { background-color: #6c757d; color: white; }

        input, textarea { width: 100%; padding: 10px; margin: 5px 0 15px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; font-family: inherit; }
        
        nav { background: #343a40; padding: 15px; color: white; border-radius: 10px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center;}
        nav a { color: white; text-decoration: none; margin-left: 20px; font-weight: 500;}
        nav span { font-weight: bold; font-size: 1.2em; }
    </style>
</head>
<body>

    <nav>
        <span>📅 Event Notifier</span>
        <div>
            <a href="/">Events</a>
            {% if session.get('logged_in') %}
                <a href="/admin">Admin Panel</a>
                <a href="/logout" style="color: #ff6b6b;">Logout</a>
            {% else %}
                <a href="/login">Admin Login</a>
            {% endif %}
        </div>
    </nav>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="flash {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <h2>{{ page_title }}</h2>

    {% if page_type == 'login' %}
        <div class="card" style="max-width: 400px; margin: auto;">
            <form method="post">
                <label>Username</label>
                <input type="text" name="username" required>
                <label>Password</label>
                <input type="password" name="password" required>
                <button type="submit" class="btn btn-blue" style="width: 100%;">Login</button>
            </form>
        </div>

    {% elif page_type == 'edit' %}
        <div class="card">
            <form method="post">
                <label>Event Title</label>
                <input type="text" name="title" value="{{ event['title'] }}" required>
                
                <label>Date (YYYY-MM-DD)</label>
                <input type="text" name="date" value="{{ event['date'] }}" required placeholder="2026-05-20">
                
                <label>Organizer (Telegram)</label>
                <input type="text" name="organizer" value="{{ event['organizer'] }}" readonly style="background: #f0f0f0;">
                
                <label>Description</label>
                <textarea name="description" rows="5" required>{{ event['description'] }}</textarea>
                
                <div style="margin-top: 15px;">
                    <button type="submit" class="btn btn-green">💾 Save Changes</button>
                    <a href="/admin" class="btn btn-grey">Cancel</a>
                </div>
            </form>
        </div>

    {% else %}
        {% for event in events %}
            <div class="card" style="border-left: 5px solid {% if event['status']=='approved' %}#28a745{% else %}#ffc107{% endif %};">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h3 style="margin-top: 0; margin-bottom: 5px;">{{ event['title'] }}</h3>
                        <span class="badge">📅 {{ event['date'] }}</span>
                        <span class="badge">👤 {{ event['organizer'] }}</span>
                    </div>
                    {% if is_admin and event['status'] == 'pending' %}
                        <span style="background: #ffc107; color: #856404; padding: 5px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold;">PENDING</span>
                    {% endif %}
                </div>
                
                <p style="color: #444; line-height: 1.6;">{{ event['description'] }}</p>
                
                {% if is_admin %}
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                    <div style="display: flex; gap: 10px;">
                        {% if event['status'] == 'pending' %}
                            <form action="/approve/{{ event['id'] }}" method="post">
                                <button type="submit" class="btn btn-green">✅ Approve</button>
                            </form>
                        {% endif %}
                        
                        <a href="/edit/{{ event['id'] }}" class="btn btn-blue">✏️ Edit</a>
                        
                        <form action="/delete/{{ event['id'] }}" method="post" onsubmit="return confirm('Delete this event?');">
                            <button type="submit" class="btn btn-red">🗑️ Delete</button>
                        </form>
                    </div>
                {% endif %}
            </div>
        {% else %}
            <div style="text-align: center; color: #777; padding: 50px;">
                <h3>No events found 📭</h3>
                <p>Wait for the Telegram Bot to send some!</p>
            </div>
        {% endfor %}
    {% endif %}
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def user_view():
    cleanup_old_events()
    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events WHERE status = "approved" ORDER BY date ASC').fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, events=events, page_title="Upcoming Events", is_admin=False, page_type='home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and user['password_hash'] == hash_password(password):
            session['logged_in'] = True
            flash("Welcome back, Admin!", "success")
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid username or password!', 'error')
    return render_template_string(HTML_TEMPLATE, events=[], page_title="Admin Login", is_admin=False, page_type='login')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('user_view'))


@app.route('/admin')
@login_required
def admin_panel():
    # cleanup_old_events()  <-- DELETE OR COMMENT THIS LINE
    conn = get_db_connection()
    # Show ALL events, even old ones, so you can see what's happening
    events = conn.execute('SELECT * FROM events ORDER BY date ASC').fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, events=events, page_title="Admin Dashboard", is_admin=True, page_type='admin')

# In app.py

from datetime import datetime

# ...

@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        title = request.form['title']
        date_input = request.form['date']
        desc = request.form['description']

        # 🛡️ FIX: Validate Date Format (YYYY-MM-DD)
        try:
            # Try to parse it. If it fails, it throws an error.
            valid_date = datetime.strptime(date_input, '%Y-%m-%d')
            
            # Update DB
            conn.execute('UPDATE events SET title = ?, date = ?, description = ? WHERE id = ?', 
                         (title, date_input, desc, event_id))
            conn.commit()
            flash("Event updated successfully!", "success")
            conn.close()
            return redirect(url_for('admin_panel'))
            
        except ValueError:
            # If format is wrong, DO NOT SAVE. Warn the user.
            flash("⚠️ Error: Date must be in YYYY-MM-DD format (e.g., 2026-12-25)", "error")
            # Reload the form with existing data
            event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
            conn.close()
            return render_template_string(HTML_TEMPLATE, events=[], event=event, page_title="Edit Event", is_admin=True, page_type='edit')

    else:
        event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
        conn.close()
        return render_template_string(HTML_TEMPLATE, events=[], event=event, page_title="Edit Event", is_admin=True, page_type='edit')
@app.route('/approve/<int:event_id>', methods=['POST'])
@login_required
def approve_event(event_id):
    conn = get_db_connection()
    conn.execute('UPDATE events SET status = "approved" WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()
    flash("Event approved and published!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()
    flash("Event deleted.", "success")
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
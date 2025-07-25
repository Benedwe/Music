#!/usr/bin/env python3
"""
A simple web application with user management functionality.
Contains several intentional bugs for demonstration purposes.
"""

import sqlite3
import os
from flask import Flask, request, jsonify, g
import time
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Fixed: Use environment variables for sensitive configuration
DATABASE = os.environ.get('DATABASE_PATH', 'users.db')
SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24).hex())

app.config['SECRET_KEY'] = SECRET_KEY

# Fixed: Proper database connection management
def get_db():
    """Get database connection with proper resource management"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.teardown_appcontext
def close_db_connection(exception):
    """Ensure database connections are closed after each request"""
    close_db()

def init_db():
    """Initialize the database"""
    conn = sqlite3.connect(DATABASE)
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                is_admin INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
    finally:
        conn.close()

@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    # Fixed: Use secure password hashing instead of MD5
    password_hash = generate_password_hash(password)
    
    conn = get_db()
    try:
        # Fixed: Using parameterized queries to prevent SQL injection
        query = "INSERT INTO users (username, password, email) VALUES (?, ?, ?)"
        conn.execute(query, (username, password_hash, email))
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 409
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    conn = get_db()
    try:
        # Fixed: Retrieve user and verify password securely
        query = "SELECT * FROM users WHERE username = ?"
        cursor = conn.execute(query, (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[2], password):  # user[2] is password field
            return jsonify({'message': 'Login successful', 'user_id': user[0]}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    finally:
        conn.close()

@app.route('/users', methods=['GET'])
def get_users():
    """Get all users - admin only"""
    # Fixed: Add authentication check (simplified for demo)
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authentication required'}), 401
    
    # Fixed: Proper input validation for page parameter
    page = request.args.get('page', '1')
    try:
        page = int(page)
        if page < 1:  # Fixed: Ensure page is positive
            page = 1
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid page parameter'}), 400
    
    # Fixed: Proper bounds checking to prevent negative offset
    offset = max(0, (page - 1) * 10)
    
    conn = get_db()
    try:
        # Check if offset is reasonable (prevent excessive memory usage)
        if offset > 10000:  # Limit to reasonable pagination
            return jsonify({'error': 'Page number too large'}), 400
            
        # Fixed: Using parameterized queries to prevent SQL injection
        query = "SELECT id, username, email FROM users LIMIT 10 OFFSET ?"
        cursor = conn.execute(query, (offset,))
        users = cursor.fetchall()
        
        # Convert to list of dicts for better JSON serialization
        users_list = [{'id': user[0], 'username': user[1], 'email': user[2]} for user in users]
        
        return jsonify({'users': users_list, 'page': page}), 200
    finally:
        conn.close()

@app.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    conn = get_db()
    try:
        # Fixed: Using parameterized queries to prevent SQL injection
        query = "DELETE FROM users WHERE id = ?"
        conn.execute(query, (user_id,))
        conn.commit()
        return jsonify({'message': 'User deleted'}), 200
    finally:
        conn.close()

# Fixed: Memory-efficient data processing with pagination
@app.route('/process_data', methods=['POST'])
def process_data():
    """Process data with memory management and pagination"""
    data = request.get_json()
    items = data.get('items', [])
    
    # Fixed: Implement pagination and memory limits
    page = int(request.args.get('page', 1))
    page_size = min(int(request.args.get('page_size', 100)), 1000)  # Max 1000 items
    
    # Calculate pagination bounds
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, len(items))
    
    if start_idx >= len(items):
        return jsonify({'processed_items': [], 'page': page, 'total_pages': 0}), 200
    
    # Fixed: Process only the current page to manage memory
    processed_items = []
    for item in items[start_idx:end_idx]:
        # Reduced processing to prevent memory bloat
        processed_item = {
            'processed': item * 2 if isinstance(item, (int, float)) else str(item).upper(),
            'timestamp': time.time()
        }
        processed_items.append(processed_item)
    
    total_pages = (len(items) + page_size - 1) // page_size
    
    return jsonify({
        'processed_items': processed_items,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'total_items': len(items)
    }), 200

if __name__ == '__main__':
    init_db()
    # Fixed: Use environment variable to control debug mode
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)
import os
import json
from functools import wraps
from flask import session, redirect, url_for, request, current_app
from werkzeug.security import check_password_hash, generate_password_hash

def load_users():
    """Load users from JSON file"""
    users_file = os.path.join(current_app.instance_path, 'users.json')
    
    # Check if users file exists
    if not os.path.exists(users_file):
        current_app.logger.warning(f"Users file not found at {users_file}. Using default admin user.")
        # Return a default admin user if file doesn't exist
        return {
            'admin': generate_password_hash('admin_password')
        }
    
    try:
        with open(users_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        current_app.logger.error(f"Error loading users file: {e}")
        # Return a default admin user if there's an error
        return {
            'admin': generate_password_hash('admin_password')
        }

def check_user_credentials(username, password):
    """Check if username and password are valid"""
    users = load_users()
    
    if username in users:
        return check_password_hash(users[username], password)
    return False

def login_required(view):
    """Decorator to require login for views"""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('auth.login', next=request.url))
        return view(*args, **kwargs)
    return wrapped_view

def add_user(username, password):
    """Add a new user or update an existing user's password"""
    users_file = os.path.join(current_app.instance_path, 'users.json')
    
    # Load existing users
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                users = json.load(f)
        except (json.JSONDecodeError, IOError):
            users = {}
    else:
        users = {}
    
    # Add or update user
    users[username] = generate_password_hash(password)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(users_file), exist_ok=True)
    
    # Save updated users
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)
    
    return True
#!/usr/bin/env python
"""
User management utility for MRI Annotation Tool

Usage:
    python manage_users.py add <username> <password>  - Add a new user or update existing user
    python manage_users.py list                       - List all users
    python manage_users.py remove <username>          - Remove a user
"""

import os
import sys
import json
from werkzeug.security import generate_password_hash

# Path to the users file
USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'users.json')

def ensure_users_file_exists():
    """Make sure the users file exists"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)

def load_users():
    """Load users from the JSON file"""
    ensure_users_file_exists()
    
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_users(users):
    """Save users to the JSON file"""
    ensure_users_file_exists()
    
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def add_user(username, password):
    """Add a new user or update an existing user"""
    users = load_users()
    users[username] = generate_password_hash(password)
    save_users(users)
    print(f"User '{username}' has been added/updated.")

def list_users():
    """List all users"""
    users = load_users()
    
    if not users:
        print("No users found.")
        return
    
    print(f"\nUsers ({len(users)}):")
    print("-" * 40)
    for username in sorted(users.keys()):
        print(f"- {username}")
    print()

def remove_user(username):
    """Remove a user"""
    users = load_users()
    
    if username not in users:
        print(f"User '{username}' not found.")
        return
    
    del users[username]
    save_users(users)
    print(f"User '{username}' has been removed.")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == 'add' and len(sys.argv) == 4:
        add_user(sys.argv[2], sys.argv[3])
    
    elif command == 'list':
        list_users()
    
    elif command == 'remove' and len(sys.argv) == 3:
        remove_user(sys.argv[2])
    
    else:
        print("Invalid command or arguments.")
        print(__doc__)

if __name__ == "__main__":
    main()

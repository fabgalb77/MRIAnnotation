import json
import os
import sys
from werkzeug.security import generate_password_hash

def create_users_file(users_file_path, users_dict):
    """
    Generate a users.json file with hashed passwords
    
    Args:
        users_file_path: Path to save the users.json file
        users_dict: Dictionary of username: password pairs
    """
    # Create hashed passwords
    users_with_hashed_passwords = {}
    for username, password in users_dict.items():
        users_with_hashed_passwords[username] = generate_password_hash(password)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(users_file_path), exist_ok=True)
    
    # Write to JSON file
    with open(users_file_path, 'w') as f:
        json.dump(users_with_hashed_passwords, f, indent=2)
    
    print(f"Created users file at {users_file_path} with {len(users_dict)} users")

if __name__ == "__main__":
    # Default path for the users file
    default_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'users.json')
    
    # Default users
    default_users = {
        "admin": "admin_password",
        "fabio": "pippo",
        "andrea": "pluto"
    }
    
    # Generate the file
    create_users_file(default_path, default_users)
    
    print("\nIMPORTANT: For security, this file contains plaintext passwords.")
    print("You should update these default passwords after the initial setup.")
    print("You can run this script again with customized values at any time.")

import json
from pprint import pprint

def view_users():
    try:
        with open('users.json', 'r') as f:
            data = json.load(f)
            
        print("\nRegistered Users:")
        print("----------------")
        for username, user in data["users"].items():
            print(f"ID: {user['id']}")
            print(f"Username: {user['username']}")
            print(f"Created at: {user['created_at']}")
            print("----------------")
    except FileNotFoundError:
        print("No users database found.")
    except json.JSONDecodeError:
        print("Error reading the database file.")

def backup_users():
    from datetime import datetime
    import shutil
    import os
    
    # Create backups directory if it doesn't exist
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/users_backup_{timestamp}.json'
    
    try:
        shutil.copy2('users.json', backup_file)
        print(f"Database backed up successfully to {backup_file}")
    except Exception as e:
        print(f"Backup failed: {e}")

def reset_users():
    response = input("Are you sure you want to reset the database? This will delete all users! (y/n): ")
    if response.lower() == 'y':
        with open('users.json', 'w') as f:
            json.dump({"users": {}}, f, indent=4)
        print("Database has been reset!")
    else:
        print("Database reset cancelled.")

if __name__ == "__main__":
    while True:
        print("\nUser Management Menu:")
        print("1. View all users")
        print("2. Backup database")
        print("3. Reset database")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            view_users()
        elif choice == '2':
            backup_users()
        elif choice == '3':
            reset_users()
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.") 
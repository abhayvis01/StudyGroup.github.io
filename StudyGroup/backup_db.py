import shutil
from datetime import datetime
import os

def backup_database():
    # Create backups directory if it doesn't exist
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/users_backup_{timestamp}.db'
    
    # Copy database file
    try:
        shutil.copy2('users.db', backup_file)
        print(f"Database backed up successfully to {backup_file}")
    except Exception as e:
        print(f"Backup failed: {e}")

if __name__ == "__main__":
    backup_database() 
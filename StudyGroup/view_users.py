import sqlite3

def view_users():
    # Connect to database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT * FROM user")
    users = cursor.fetchall()
    
    # Print users
    print("\nRegistered Users:")
    print("----------------")
    for user in users:
        print(f"ID: {user[0]}")
        print(f"Username: {user[1]}")
        print(f"Created at: {user[3]}")
        print("----------------")
    
    conn.close()

if __name__ == "__main__":
    view_users() 
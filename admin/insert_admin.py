from werkzeug.security import generate_password_hash
import psycopg2
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Create and manage a database connection."""
    conn = None
    try:
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            dbname='postgres',
            user='postgres',
            password='200408'
        )
        cur = conn.cursor()
        yield conn, cur
    finally:
        if conn is not None:
            conn.close()

def hash_password(password, method='pbkdf2:sha256', salt_length=16):
    return generate_password_hash(password, method=method, salt_length=salt_length)

def insert_admin(admin_id, name, email, password):
    try:
        hashed_password = hash_password(password)
        
        with get_db_connection() as (conn, cur):
            cur.execute("SELECT * FROM admin WHERE email = %s", (email,))
            if cur.fetchone() is not None:
                return False, "Email already registered"
            
            cur.execute("SELECT * FROM admin WHERE admin_id = %s", (admin_id,))
            if cur.fetchone() is not None:
                return False, "Admin ID already exists"
            
            insert_query = """
                INSERT INTO admin (admin_id, name, email, password)
                VALUES (%s, %s, %s, %s);
            """
            cur.execute(insert_query, (admin_id, name, email, hashed_password))
            
            conn.commit()
            return True, f"Admin with ID {admin_id} successfully added"
            
    except Exception as error:
        return False, str(error)

def main():
    print("=== Add New Admin ===")
    try:
        admin_id = int(input("Enter admin ID: "))
        name = input("Enter admin name: ")
        email = input("Enter admin email: ")
        password = input("Enter admin password: ")
        
        success, result = insert_admin(admin_id, name, email, password)
        
        if success:
            print(result)
        else:
            print(f"Failed to add admin: {result}")
    except ValueError:
        print("Error: Admin ID must be a number")

if __name__ == "__main__":
    main()
    
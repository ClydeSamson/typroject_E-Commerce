import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        dbname='post',
        user='postgres',
        password='Project10'
    )
    cur = conn.cursor()
    create_table_pro = '''
    CREATE TABLE IF NOT EXISTS products (
        product_id SERIAL PRIMARY KEY,
        product_name VARCHAR(100) NOT NULL,
        description VARCHAR(500) NOT NULL UNIQUE,
        category VARCHAR(200) NOT NULL,
        size VARCHAR(30) NOT NULL,
        price INTEGER NOT NULL,
        image BYTEA   
    );
    '''
    create_table_log = '''
    CREATE TABLE IF NOT EXISTS login (
        id SERIAL PRIMARY KEY,
        email VARCHAR(100) NOT NULL,
        password VARCHAR(512) NOT NULL UNIQUE  
    );
    '''
    create_table_complaints = '''
        CREATE TABLE IF NOT EXISTS complaints (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL,
        subject VARCHAR(350) NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES login(id) ON DELETE CASCADE
    );
    '''
    create_table_customer = '''
        CREATE TABLE IF NOT EXISTS customer (
        customer_id SERIAL PRIMARY KEY,
        customer_name VARCHAR(100) NOT NULL,
        address VARCHAR(200) NOT NULL,
        landmark VARCHAR(100) NOT NULL,
        city varchar(100) NOT NULL,
        state varchar(100) NOT NULL,
        pincode INTEGER NOT NULL,
        phone_number INTEGER NOT NULL,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES login(id) ON DELETE CASCADE
    );
    '''
    create_table_cart = '''
        CREATE TABLE IF NOT EXISTS cart (
        cart_id SERIAL PRIMARY KEY,
        customer_id INTEGER,
        product_id INTEGER,
        quantity INTEGER DEFAULT 1,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES login(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
    );
    '''

    
    cur.execute(create_table_pro)
    cur.execute(create_table_log)
    cur.execute(create_table_complaints)
    cur.execute(create_table_customer)
    cur.execute(create_table_cart)
    try:
        yield conn
    finally:
        conn.close()

class logclass():
    def verify_login(self, email, password):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()

                cur.execute("SELECT id, email, password FROM login WHERE email = %s", (email,))
                user = cur.fetchone()
                
                if user is None:
                    return False, "Email not found"
                
                stored_password = user[2]
                if check_password_hash(stored_password, password):
                    return True, user[0]  
                else:
                    return False, "Incorrect password"
                
        except Exception as error:
            return False, str(error)

    def create_user(self, email, password):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                hashed_password = generate_password_hash(password)
                
                cur.execute("SELECT * FROM login WHERE email = %s", (email,))
                if cur.fetchone() is not None:
                    return False, "Email already registered"
                
                insert_query_login = """
                    INSERT INTO login (email, password)
                    VALUES (%s, %s)
                    RETURNING id;
                """
                cur.execute(insert_query_login, (email, hashed_password))
                user_id = cur.fetchone()[0]
                
                conn.commit()
                return True, user_id
                
        except Exception as error:
            return False, str(error)
        
class add_product_db():
    def add_product(self, product_id, product_name, description, category, size, price, image):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Check if product already exists
                cur.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
                if cur.fetchone() is not None:
                    return False, "Product ID already exists"
                
                # Insert new product
                insert_query_addpro = """
                    INSERT INTO products (product_id, product_name, description, category, size, price, image)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """
                cur.execute(insert_query_addpro, (product_id, product_name, description, category, size, price, image))
                
                conn.commit()
                return True, "Product added successfully"
                
        except Exception as error:
            return False, str(error)
    
    def get_all_products(self):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                cur.execute("SELECT product_id, product_name, description, category, size, price FROM products")
                products = cur.fetchall()
                
                return products
                
        except Exception as error:
            return []
        
class comp_db():
    def submit_contact_form(self, name, email, subject, message, user_id=None):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
            
                insert_query = """
                    INSERT INTO complaints (name, email, subject, message, user_id)
                    VALUES (%s, %s, %s, %s, %s);
                """
                cur.execute(insert_query, (name, email, subject, message, user_id))
            
                conn.commit()
                return True, "Your message has been sent successfully! We will notify through email"
            
        except Exception as error:
            return False, str(error)

class cart_db():
    def add_to_cart(self, customer_id, product_id, quantity=1):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Check if product already in cart
                cur.execute("SELECT cart_id, quantity FROM cart WHERE customer_id = %s AND product_id = %s", 
                           (customer_id, product_id))
                existing_cart_item = cur.fetchone()
                
                if existing_cart_item:
                    # Update quantity
                    cart_id, current_quantity = existing_cart_item
                    new_quantity = current_quantity + quantity
                    
                    update_query = """
                        UPDATE cart 
                        SET quantity = %s 
                        WHERE cart_id = %s
                    """
                    cur.execute(update_query, (new_quantity, cart_id))
                    
                else:
                    # Add new item to cart
                    insert_query = """
                        INSERT INTO cart (customer_id, product_id, quantity)
                        VALUES (%s, %s, %s)
                    """
                    cur.execute(insert_query, (customer_id, product_id, quantity))
                
                conn.commit()
                return True, "Product added to cart successfully"
                
        except Exception as error:
            return False, str(error)
            
    def get_cart_items(self, customer_id):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                query = """
                    SELECT c.cart_id, p.product_id, p.product_name, p.price, c.quantity, 
                           (p.price * c.quantity) as total_price
                    FROM cart c
                    JOIN products p ON c.product_id = p.product_id
                    WHERE c.customer_id = %s
                """
                cur.execute(query, (customer_id,))
                cart_items = cur.fetchall()
                
                return cart_items
                
        except Exception as error:
            return []

class customer_db():
    def add_customer_details(self, customer_name, address, landmark, city, state, pincode, 
                           phone_number, user_id):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Check if customer details already exist
                cur.execute("SELECT * FROM customer WHERE user_id = %s", (user_id,))
                if cur.fetchone() is not None:
                    # Update existing details
                    update_query = """
                        UPDATE customer
                        SET customer_name = %s, address = %s, landmark = %s, city = %s,
                            state = %s, pincode = %s, phone_number = %s
                        WHERE user_id = %s
                    """
                    cur.execute(update_query, (customer_name, address, landmark, city, 
                                             state, pincode, phone_number, user_id))
                    
                    conn.commit()
                    return True, "Customer details updated successfully"
                
                # Insert new customer details
                insert_query = """
                    INSERT INTO customer (customer_name, address, landmark, city, state, 
                                         pincode, phone_number, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(insert_query, (customer_name, address, landmark, city, 
                                         state, pincode, phone_number, user_id))
                
                conn.commit()
                return True, "Customer details added successfully"
                
        except Exception as error:
            return False, str(error)
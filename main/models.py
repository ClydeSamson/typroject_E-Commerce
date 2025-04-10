# import pandas as pd
import pickle
import psycopg2
import os
import re
import difflib
# from sklearn.ensemble import GradientBoostingClassifier
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import LabelEncoder
# from sklearn.feature_extraction.text import TfidfVectorizer
from main import db
from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import contextmanager
from flask import Flask, request, jsonify
# from sklearn.metrics.pairwise import cosine_similarity

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        dbname='postgres',
        user='postgres',
        password='200408'
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
        landmark VARCHAR(100),
        city varchar(100) NOT NULL,
        state varchar(100) NOT NULL,
        pincode varchar(30) NOT NULL,
        phone_number varchar(100) NOT NULL,
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
    create_table_orders = '''
    CREATE TABLE IF NOT EXISTS orders (
        order_id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        payment_method VARCHAR(50) DEFAULT 'COD',
        order_status VARCHAR(50) DEFAULT 'Pending',
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES login(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
    );
'''

    
    cur.execute(create_table_pro)
    cur.execute(create_table_log)
    cur.execute(create_table_complaints)
    cur.execute(create_table_customer)
    cur.execute(create_table_cart)
    cur.execute(create_table_orders)
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
    def get_complaints():
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
        
        # Query to fetch all complaints, ordered by most recent first
                cur.execute("""
                SELECT id, name, email, subject, message, created_at 
                FROM complaints 
                ORDER BY created_at DESC
                """)
        
            # Fetch all complaints
                complaints = cur.fetchall()
        
            # Convert to list of dictionaries for easier template rendering
                complaint_list = [
                {
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'subject': row[3],
                'message': row[4],
                'created_at': row[5].strftime('%Y-%m-%d %H:%M:%S')
                }
                for row in complaints
                ]
                return complaint_list
    
        except Exception as e:
            print(f"Error fetching complaints: {e}")
            return []

class cart_db:
    def get_cart_items(self, user_id):
        """
        Retrieve all cart items for a specific user.
        Returns a list of tuples with format:
        (item_id, product_name, product_image, quantity, unit_price, total_price)
        """
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
            
                query = """
                SELECT c.cart_id, p.product_name, p.image, c.quantity, p.price, (c.quantity * p.price) as total_price
                FROM cart c
                JOIN products p ON c.product_id = p.product_id
                WHERE c.customer_id = %s
                """
                cur.execute(query, (user_id,))
            
                # Convert the binary image data
                results = cur.fetchall()
                processed_results = []
            
                for row in results:
                    # Create a new tuple with processed image data (binary to base64 if needed)
                    # If the image is None, keep it as None
                    if row[2] is not None:
                        # Convert memoryview to bytes
                        image_bytes = bytes(row[2])
                        processed_row = (row[0], row[1], image_bytes, row[3], row[4], row[5])
                    else:
                        processed_row = row
                    
                    processed_results.append(processed_row)
                
                return processed_results
        except Exception as e:
            print(f"Error getting cart items: {e}")
            return []
    
    def update_item_quantity(self, user_id, item_id, quantity):
        """
        Update the quantity of a specific cart item.
        Returns True if successful, False otherwise.
        """
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                query = """
                    UPDATE cart
                    SET quantity = %s
                    WHERE customer_id = %s AND cart_id = %s
                """
                cur.execute(query, (quantity, user_id, item_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating cart: {e}")
            return False
    
    def remove_item(self, user_id, item_id):
        """
        Remove a specific item from the user's cart.
        Returns True if successful, False otherwise.
        """
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                query = """
                    DELETE FROM cart
                    WHERE customer_id = %s AND cart_id = %s
                """
                cur.execute(query, (user_id, item_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error removing item from cart: {e}")
            return False
            
    def add_to_cart(self, user_id, product_id, quantity=1):
        """
        Add a product to the user's cart.
        If the product is already in the cart, update its quantity.
        Returns True if successful, False otherwise.
        """
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Check if the item is already in the cart
                cur.execute(
                    "SELECT cart_id, quantity FROM cart WHERE customer_id = %s AND product_id = %s",
                    (user_id, product_id)
                )
                existing_item = cur.fetchone()
                
                if existing_item:
                    # Update quantity of existing item
                    new_quantity = existing_item[1] + quantity
                    cur.execute(
                        "UPDATE cart SET quantity = %s WHERE cart_id = %s",
                        (new_quantity, existing_item[0])
                    )
                else:
                    # Add new item to cart
                    cur.execute(
                        "INSERT INTO cart (customer_id, product_id, quantity) VALUES (%s, %s, %s)",
                        (user_id, product_id, quantity)
                    )
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding item to cart: {e}")
            return False
    

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
        
class orders_db():
    def get_all_orders(self):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                query = """
                SELECT o.order_id, l.email, p.product_name, o.amount, o.payment_method, o.order_status, o.added_at
                FROM orders o
                JOIN login l ON o.user_id = l.id
                JOIN products p ON o.product_id = p.product_id
                ORDER BY o.added_at DESC
                """
                cur.execute(query)
                orders = cur.fetchall()
                
                return orders
                
        except Exception as error:
            print(f"Error fetching orders: {error}")
            return []
    
    def update_order_status(self, order_id, new_status):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                query = """
                UPDATE orders
                SET order_status = %s
                WHERE order_id = %s
                """
                cur.execute(query, (new_status, order_id))
                conn.commit()
                
                return True, "Order status updated successfully"
                
        except Exception as error:
            return False, str(error)

class ProductRecommendations:
    def get_cross_sell_products(self, product_name, description, product_id, limit=4):
        """
        Fetch cross-sell products based on product type (not category).
        """
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Determine what to cross-sell based on product type
                if "hoodie" in product_name.lower() or "hoodie" in description.lower():
                    cross_sell_types = ['pants', 'shoes']
                elif "t-shirt" in product_name.lower() or "t-shirt" in description.lower():
                    cross_sell_types = ['pants', 'shoes']
                elif "pants" in product_name.lower() or "pants" in description.lower():
                    cross_sell_types = ['t-shirt', 'hoodie', 'shoes']
                elif "shoes" in product_name.lower() or "shoes" in description.lower():
                    cross_sell_types = ['pants', 't-shirt', 'hoodie']
                else:
                    cross_sell_types = []
                
                if cross_sell_types:
                    query = f"""
                        SELECT product_id, product_name, description, price, image
                        FROM products
                        WHERE product_id != %s AND (
                            {' OR '.join(["LOWER(product_name) LIKE %s" for _ in cross_sell_types])}
                        )
                        ORDER BY RANDOM()
                        LIMIT %s
                    """
                    cur.execute(query, (product_id, *[f'%{ptype}%' for ptype in cross_sell_types], limit))
                else:
                    return []
                
                cross_sell_products = [
                    {
                        'product_id': row[0],
                        'product_name': row[1],
                        'description': row[2],
                        'price': row[3],
                        'image_url': f"/static/images/product{row[0]}.jpg" if row[4] else "/static/images/default_product.jpg"
                    }
                    for row in cur.fetchall()
                ]
                
                return cross_sell_products
        
        except Exception as error:
            print(f"Database error in cross-sell: {error}")
            return []

    def get_upsell_products(self, product_id, category, product_name, price, limit=4):
        """
        Fetch upsell products with a higher price of the same product type in the same category.
        """
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Identify product type keyword (hoodie, t-shirt, pants, shoes, etc.)
                if "hoodie" in product_name.lower():
                    product_type = "hoodie"
                elif "t-shirt" in product_name.lower():
                    product_type = "t-shirt"
                elif "pants" in product_name.lower():
                    product_type = "pants"
                elif "shoes" in product_name.lower():
                    product_type = "shoes"
                else:
                    product_type = product_name.split()[0] if product_name else ''
                
                # Query to fetch upsell products of the same type with a higher price
                query = """
                    SELECT product_id, product_name, description, price, image
                    FROM products
                    WHERE category = %s AND product_id != %s AND price > %s AND LOWER(product_name) LIKE %s
                    ORDER BY price ASC
                    LIMIT %s
                """
                cur.execute(query, (category, product_id, price, f'%{product_type.lower()}%', limit))
                
                upsell_products = cur.fetchall()
                
                return [
                    {
                        'product_id': row[0],
                        'product_name': row[1],
                        'description': row[2],
                        'price': row[3],
                        'image_url': f"/static/images/product{row[0]}.jpg" if row[4] else "/static/images/default_product.jpg"
                    }
                    for row in upsell_products
                ]
        
        except Exception as error:
            print(f"Database error in upsell: {error}")
            return []

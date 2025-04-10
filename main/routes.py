from flask import render_template, flash, redirect, url_for,request,jsonify,session, Response,Blueprint,send_from_directory,abort
from main import app,ALLOWED_EXTENSIONS,db
from main.forms import LoginForm,SignupForm,ProductForm
from datetime import datetime, timedelta
from .models import logclass,add_product_db,get_db_connection,comp_db,cart_db,customer_db,orders_db
import os
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
import base64
from .models import ProductRecommendations
from flask import Flask, render_template, request
from .models import add_product_db
import base64
from flask import Blueprint

app.jinja_env.filters['b64encode'] = lambda b: base64.b64encode(b).decode()

@app.route('/')
@app.route('/home')
def home():
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT product_id, product_name, description, category, size, price, image FROM products")
            product_data = cur.fetchall()
            
        products = []
        for product in product_data:
            icon = "tag"
            if product[3] == "male":
                icon = "person"
            elif product[3] == "female":
                icon = "person-heart"
            elif product[3] == "kids":
                icon = "people"
                
            image_path = f"product_{product[0]}.jpg"
            
            products.append({
                'id': product[0],
                'name': product[1],
                'description': product[2],
                'category': product[3],
                'size': product[4],
                'price': product[5],
                'icon': icon,
                'image': image_path  
            })
            
        return render_template('home.html', products=products)
    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        return render_template('home.html', products=[])

@app.route('/static/images/product_<int:product_id>.jpg')
def serve_static_product_image(product_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT image FROM products WHERE product_id = %s", (product_id,))
            image_data = cur.fetchone()
            
            if image_data and image_data[0]:
                return app.response_class(image_data[0], mimetype='image/jpeg')
            else:
                return redirect(url_for('static', filename='images/placeholder.jpg'))
    except Exception as e:
        print(f"Error retrieving product image: {str(e)}")
        return redirect(url_for('static', filename='images/placeholder.jpg'))
    
###
@app.route('/filtered_products', methods=['GET', 'POST'])
def filtered_products():
    filters = {}  # Dictionary to store filter conditions
    query = "SELECT product_id, product_name, description, category, size, price, image FROM products WHERE 1=1"
    values = []

    # Retrieve filter values from the form
    category = request.form.get('category')
    size = request.form.get('size')
    min_price = request.form.get('min_price')
    max_price = request.form.get('max_price')

    # Apply filters dynamically
    if category:
        query += " AND category = %s"
        values.append(category)
    if size:
        query += " AND size = %s"
        values.append(size)
    if min_price:
        query += " AND price >= %s"
        values.append(min_price)
    if max_price:
        query += " AND price <= %s"
        values.append(max_price)

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, tuple(values))
        filtered_products = cur.fetchall()

    return render_template('filtered_products.html', products=filtered_products)


###

############################################################################################################################################### 
@app.route('/product-image/<int:product_id>')
def serve_product_image(product_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT image FROM products WHERE product_id = %s", (product_id,))
            image_data = cur.fetchone()[0]
            
            if image_data:
                return Response(image_data, mimetype='image/jpeg')
            else:
                return redirect(url_for('static', filename='images/no-image.jpg'))
    except Exception as e:
        print(f"Error serving product image: {str(e)}")
        return redirect(url_for('static', filename='images/no-image.jpg'))

###################################################################################################   
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        db = logclass()
        success, message = db.create_user(form.email.data, form.password.data)
        
        if success:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(f'Registration failed: {message}', 'danger')
            
    return render_template('signup.html', form=form, title='Sign Up - Urban Style')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        # First, check if it's an admin login
        admin_user = None
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT admin_id, email, password FROM admin WHERE email = %s", (email,))
                admin_user = cur.fetchone()
        except Exception as e:
            flash(f'Database error: {str(e)}', 'danger')
            return render_template('login.html', title='Login Page', form=form)
        
        # If admin credentials found, verify password
        if admin_user:
            # Check if the password matches - assuming direct comparison or using check_password_hash
            # You might need to adjust this based on how admin passwords are stored
            if check_password_hash(admin_user[2], password):
                session['admin_id'] = admin_user[0]
                session['email'] = email
                session['is_admin'] = True
                
                if form.remember.data:
                    session.permanent = True
                    app.permanent_session_lifetime = timedelta(days=30)
                
                flash('Admin login successful!', 'success')
                return redirect(url_for('dashboard'))  # Redirect to admin dashboard
            else:
                flash('Invalid admin credentials!', 'danger')
                return render_template('login.html', title='Login Page', form=form)
        
        # If not admin, try customer login
        db_handler = logclass()
        success, user_id = db_handler.verify_login(email, password)
        
        if success:
            # Store user information in session
            session['user_id'] = user_id
            session['email'] = email
            session['is_admin'] = False
            
            if form.remember.data:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            
            flash('Login successful!', 'success')
            
            # Redirect to next page if specified
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            flash(f'Login failed: {user_id}', 'danger')
    
    return render_template('login.html', title='Login Page', form=form)

# Logout route update
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))
#########################################################################################################   
stats = [
    {"icon": "bi bi-people-fill", "number": "10,000+", "text": "Happy Customers"},
    {"icon": "bi bi-bag-check-fill", "number": "5,000+", "text": "Products Sold"},
    {"icon": "bi bi-globe", "number": "25+", "text": "Countries Served"},
    {"icon": "bi bi-star-fill", "number": "4.8", "text": "Average Rating"}
]

values = [
    {"icon": "bi bi-heart-fill", "title": "Quality", "text": "We believe in creating products that stand the test of time, using premium materials and expert craftsmanship."},
    {"icon": "bi bi-leaf-fill", "title": "Sustainability", "text": "Our commitment to the environment drives us to use eco-friendly materials and ethical production methods."},
    {"icon": "bi bi-people-fill", "title": "Community", "text": "We foster a sense of belonging among our customers and give back to the communities we serve."}
]
@app.route('/about', methods=['GET', 'POST'])
def about():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        user_id = session.get('user_id')
        
        success, msg = comp_db.submit_contact_form(name, email, subject, message, user_id)
        
        if success:
            flash(msg, 'success')
        else:
            flash(f'Error: {msg}', 'danger')
            
        return redirect(url_for('home'))
    
    return render_template('about.html', stats=stats, values=values)

####################################################################################################

@app.route('/checkout/<int:product_id>')
def direct_checkout(product_id):
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to continue to checkout', 'warning')
        return redirect(url_for('login', next=request.url))
    
    user_id = session['user_id']
    
    # Get product details
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Fetch the specific product
        cur.execute("""
            SELECT product_id, product_name, description, category, size, price, image 
            FROM products 
            WHERE product_id = %s
        """, (product_id,))
        product = cur.fetchone()
        
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('index'))
        
        # Fetch customer details
        cur.execute("""
            SELECT customer_name, address, landmark, city, state, pincode, phone_number
            FROM customer
            WHERE user_id = %s
        """, (user_id,))
        customer_data = cur.fetchone()
    
    # Calculate pricing details
    discount_percentage = 10
    original_price = round(product[5] / (1 - discount_percentage/100), 2)
    
    # Handle image conversion
    image_data = None
    if product[6] is not None:
        try:
            # Convert memoryview to bytes, then to base64 if needed
            image_bytes = bytes(product[6])
            image_data = base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error converting image: {e}")
            image_data = None
    
    # Create processed items list with single product
    processed_items = [{
        'id': product[0],
        'name': product[1],
        'size': product[4],
        'seller': 'Urban Style',
        'price': product[5],
        'original_price': original_price,
        'discount': discount_percentage,
        'quantity': 1,
        'total_price': product[5],
        'image': image_data  # Now a base64 string or None
    }]
    
    subtotal = product[5]
    shipping = 0 if subtotal >= 1000 else 100
    total = subtotal + shipping
    
    # Prepare customer data
    customer = None
    if customer_data:
        customer = {
            'name': customer_data[0],
            'street': customer_data[1],
            'landmark': customer_data[2] if customer_data[2] else '',
            'city': customer_data[3],
            'state': customer_data[4],
            'pincode': customer_data[5],
            'phone': customer_data[6]
        }
    
    return render_template('checkout.html',
                           products=processed_items,
                           subtotal=subtotal,
                           shipping=shipping,
                           total=total,
                           customer=customer)

@app.route('/place_order', methods=['POST'])
def place_order():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to place an order', 'warning')
        return jsonify({
            'success': False, 
            'message': 'User not logged in'
        }), 401
    
    user_id = session['user_id']
    
    # Get order details from form/JSON
    try:
        # Try to get data from JSON first, then form
        if request.is_json:
            order_data = request.get_json()
            products = order_data.get('products', [])
            total_amount = order_data.get('total_amount')
            payment_method = order_data.get('payment_method', 'COD')
        else:
            products = request.form.getlist('products')
            total_amount = request.form.get('total_amount')
            payment_method = request.form.get('payment_method', 'COD')
        
        # Validate required fields
        if not products or not total_amount:
            return jsonify({
                'success': False, 
                'message': 'Missing product or amount details'
            }), 400
        
        try:
            total_amount = float(total_amount)  # Ensure amount is a number
        except ValueError:
            return jsonify({
                'success': False, 
                'message': 'Invalid amount'
            }), 400
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Store order IDs to return
            order_ids = []
            
            # Insert each product as a separate order
            for product in products:
                # If products are passed as JSON, extract details
                if isinstance(product, dict):
                    product_id = product.get('product_id')
                    product_amount = product.get('amount', total_amount)
                else:
                    # If products are simple list of IDs
                    product_id = product
                    product_amount = total_amount
                
                # Verify product exists
                cur.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
                if not cur.fetchone():
                    return jsonify({
                        'success': False, 
                        'message': f'Product {product_id} not found'
                    }), 404
                
                # Insert order into orders table
                insert_query = """
                INSERT INTO orders (user_id, product_id, amount, payment_method)
                VALUES (%s, %s, %s, %s)
                RETURNING order_id
                """
                cur.execute(insert_query, (user_id, product_id, product_amount, payment_method))
                
                # Get the new order ID
                order_id = cur.fetchone()[0]
                order_ids.append(order_id)
            
            conn.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Order placed successfully',
                'order_ids': order_ids,
                'total_orders': len(order_ids)
            }), 200
    
    except Exception as e:
        print(f"Error placing order: {e}")
        return jsonify({
            'success': False, 
            'message': 'An unexpected error occurred while placing the order'
        }), 500
    
@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    try:
        # Connect to database
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Get order details
            cur.execute("""
                SELECT o.order_id, o.amount, o.added_at, 
                       p.product_name, p.product_id, p.size
                FROM orders o
                JOIN products p ON o.product_id = p.product_id
                WHERE o.order_id = %s AND o.user_id = %s
            """, (order_id, user_id))
            
            order_data = cur.fetchone()
            
            if not order_data:
                # Handle case where order doesn't exist or doesn't belong to user
                return render_template('error.html', message="Order not found"), 404
            
            # Get customer details
            cur.execute("""
                SELECT customer_name, address, landmark, city, state, pincode, phone_number
                FROM customer
                WHERE user_id = %s
            """, (user_id,))
            
            customer_data = cur.fetchone()
            
            # Create order object for template
            order = {
                'id': order_data[0],
                'amount': order_data[1],
                'date': order_data[2].strftime('%B %d, %Y'),
                'product_name': order_data[3],
                'product_image': f"product_{order_data[4]}.jpg",  # Using product_id for image
                'size': order_data[5]
            }
            
            # Create customer object for template
            if customer_data:
                customer = {
                    'name': customer_data[0],
                    'street': customer_data[1],
                    'landmark': customer_data[2] if customer_data[2] else '',
                    'city': customer_data[3],
                    'state': customer_data[4],
                    'pincode': customer_data[5],
                    'phone': customer_data[6]
                }
            else:
                # Handle case where customer details don't exist
                customer = {}
            delivery_date = (datetime.now() + timedelta(days=5)).strftime('%B %d, %Y')
            
            return render_template('order_confirmation.html', 
                               order=order,
                               customer=customer,
                               delivery_date=delivery_date)
                               
    except Exception as e:
        print(f"Error processing order confirmation: {e}")
        return render_template('error.html', message="Error retrieving order details"), 500
    

@app.route('/save_address', methods=['POST'])
def save_address():
    try:
        # Get data from request - handle both JSON and form data
        if request.is_json:
            address_data = request.json
        else:
            address_data = {
                'name': request.form.get('name'),
                'address': request.form.get('street'),
                'landmark': request.form.get('landmark'),
                'city': request.form.get('city'),
                'state': request.form.get('state'),
                'pincode': request.form.get('pincode'),
                'phone': request.form.get('phone')
            }
        
        # Verify that we have a user in the session
        if 'user_id' not in session:
            return jsonify({
                'status': 'error',
                'message': 'User not logged in'
            }), 401
            
        user_id = session['user_id']
        
        # Instantiate customer database handler
        customer_handler = customer_db()
        
        # Save customer details
        success, message = customer_handler.add_customer_details(
            customer_name=address_data.get('name'),
            address=address_data.get('address'),
            landmark=address_data.get('landmark'),
            city=address_data.get('city'),
            state=address_data.get('state'),
            pincode=address_data.get('pincode'),
            phone_number=address_data.get('phone'),
            user_id=user_id
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'address': address_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 500
            
    except Exception as e:
        print(f"Error saving address: {str(e)}")  # Log the error
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

#####################################   admin   ###############################################

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')
######################################################################################################
@app.route('/product_image/<int:product_id>')
def admin_product_image(product_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT image FROM users WHERE product_id = %s", (product_id,))
            image_data = cur.fetchone()[0]
            
            if image_data:
                return app.response_class(image_data, mimetype='image/jpeg')
            else:
                return redirect(url_for('static', filename='images/placeholder.jpg'))
    except Exception as e:
        print(f"Error retrieving image: {str(e)}")
        return redirect(url_for('static', filename='images/placeholder.jpg'))
    
@app.route('/dashboard/add_product', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()

    if request.method == 'POST':
        category = request.form.get('category')
        if category == 'male':
            form.size.choices = [('', 'Select Size')] + [(s, s) for s in ['S', 'M', 'L', 'XL', 'XXL']]
        elif category == 'female':
            form.size.choices = [('', 'Select Size')] + [(s, s) for s in ['XS', 'S', 'M', 'L', 'XL']]
        elif category == 'kids':
            form.size.choices = [('', 'Select Size')] + [(s, s) for s in ['7', '8', '9']]
    
    if form.validate_on_submit():
        try:
            image_file = form.image.data
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                file_ext = os.path.splitext(filename)[1]
                unique_filename = f"{form.pid.data}_{form.size.data}{file_ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                image_file.save(file_path)
                
                with open(file_path, 'rb') as f:
                    image_binary = f.read()
                
                product_db = add_product_db()
                success, message = product_db.add_product(
                    form.pid.data,
                    form.pname.data,
                    form.description.data,
                    form.category.data,
                    form.size.data,
                    form.price.data,
                    image_binary
                )
                
                if success:
                    flash('Product added successfully!', 'success')
                else:
                    flash(f'Failed to add product: {message}', 'danger')
                    
                return redirect(url_for('add_product'))
            else:
                flash('Invalid file format. Allowed formats are png, jpg, jpeg, gif, and webp', 'danger')
                
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('add_product.html', form=form)
####################################################################################################################
@app.route('/dashboard/remove_product', methods=['GET'])
def remove_product():
    try:
        print("Starting to fetch products for removal page...")
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Check if the products table exists and has records (fixed query)
            cur.execute("SELECT COUNT(*) FROM products")
            count = cur.fetchone()[0]
            print(f"Found {count} products in database")
            
            if count == 0:
                print("No products found in the database")
                flash('No products found in the database.', 'warning')
                return render_template('remove_product.html', products=[], error="No products found")
            
            # Fetch the products
            cur.execute("SELECT product_id, product_name, category, size, price FROM products")
            products = cur.fetchall()
            print(f"Successfully fetched {len(products)} products")
            
            # Debug the first product if available
            if products and len(products) > 0:
                print(f"First product data: {products[0]}")

            formatted_products = [
                {'id': p[0], 'name': p[1], 'category': p[2], 'size': p[3], 'price': p[4]} 
                for p in products
            ]

            return render_template('remove_product.html', products=formatted_products)
    except Exception as e:
        detailed_error = f"Error fetching products for removal: {str(e)}"
        print(detailed_error)
        import traceback
        print(traceback.format_exc())
        flash(detailed_error, 'danger')
        return render_template('remove_product.html', products=[], error=detailed_error)


@app.route('/api/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM products WHERE product_id = %s", (product_id,))
            count = cur.fetchone()[0]
            
            if count == 0:
                return jsonify({
                    'success': False,
                    'message': f'Product with ID {product_id} not found'
                }), 404
            
            cur.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Product with ID {product_id} deleted successfully'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleting product: {str(e)}'
        }), 500
    

@app.route('/api/products', methods=['GET'])
def api_products():
    try:
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Base query
            query = "SELECT product_id, product_name, category, size, price FROM products WHERE 1=1"
            params = []
            
            # Add search filter if provided
            if search:
                query += " AND (product_name ILIKE %s OR description ILIKE %s)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            # Add category filter if provided
            if category:
                query += " AND category = %s"
                params.append(category)
            
            # Execute the query
            cur.execute(query, params)
            products = cur.fetchall()
            
            # Format the results
            formatted_products = [
                {
                    'id': p[0], 
                    'name': p[1], 
                    'category': p[2], 
                    'size': p[3], 
                    'price': p[4]
                } 
                for p in products
            ]
            
            return jsonify({
                'success': True,
                'products': formatted_products
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/dashboard/update_inventory', methods=['GET'])
def update_inventory():
    """Route to render the update inventory page"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Check if stock column exists
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='products' AND column_name='stock'")
            stock_column_exists = cur.fetchone() is not None
            
            if not stock_column_exists:
                # Add stock column if it doesn't exist
                cur.execute("ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 0")
                conn.commit()
            
            # Now fetch products with all columns including stock
            cur.execute("SELECT product_id, product_name, category, size, price, stock, image FROM products")
            products_data = cur.fetchall()
            
            print(f"Products fetched from database: {len(products_data)}")
            
            products = []
            for product in products_data:
                # Create a unique image path based on product ID
                image_path = f"product_{product[0]}.jpg"
                
                products.append({
                    'id': product[0],
                    'name': product[1],
                    'category': product[2],
                    'size': product[3],
                    'price': product[4],
                    'stock': product[5] or 0,  # Use 0 if stock is None
                    'image': image_path
                })
            
            print(f"Processed products: {len(products)}")
            return render_template('update_inventory.html', products=products)
    except Exception as e:
        print(f"Error fetching products for inventory update: {str(e)}")
        flash('Error loading products. Please try again later.', 'danger')
        return render_template('update_inventory.html', products=[])

@app.route('/api/update_inventory', methods=['POST'])
def api_update_inventory():
    """API endpoint to handle inventory updates"""
    try:
        data = request.json
        updated_products = data.get('products', [])
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            for product in updated_products:
                # Check if the stock column exists in the products table
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='products' AND column_name='stock'")
                stock_column_exists = cur.fetchone() is not None
                
                if not stock_column_exists:
                    # Add stock column if it doesn't exist
                    cur.execute("ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 0")
                    conn.commit()
                
                # Update the product price and stock
                cur.execute(
                    "UPDATE products SET price = %s, stock = %s WHERE product_id = %s",
                    (product['price'], product['stock'], product['id'])
                )
            
            conn.commit()
            
        return jsonify({
            'success': True,
            'message': 'Inventory updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating inventory: {str(e)}'
        }), 500

@app.route('/orders', methods=['GET', 'POST'])
def orders_page():
    # Initialize the orders database class
    orders_model = orders_db()
    
    # Fetch all orders
    all_orders = orders_model.get_all_orders()
    
    # Handle order status updates (if form submitted)
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        new_status = request.form.get('new_status')
        
        if order_id and new_status:
            success, message = orders_model.update_order_status(order_id, new_status)
            if success:
                flash(message, 'success')
            else:
                flash(message, 'danger')
            
            # Redirect to avoid form resubmission
            return redirect(url_for('orders_page'))
    
    # Pass the orders to the template
    return render_template('order_templet.html', orders=all_orders)
########################################################################################################
@app.route('/allproducts')  # Or potentially '/all-products'
def all_products():
    products_list = add_product_db().get_all_products()
    products = [
        {
            'id': product[0],
            'name': product[1],
            'description': product[2],
            'category': product[3],
            'size': product[4],
            'price': product[5],
            'image': f'product{product[0]}.jpg'  # Consistent image naming
        }
        for product in products_list
    ]
    
    return render_template('all_products.html', products=products)

@app.route('/images/<filename>')
def get_image(filename):
    try:
        image_directory = os.path.join(app.root_path, 'static', 'uploads')
        
        return send_from_directory(image_directory, filename)
    
    except FileNotFoundError:
        abort(404)

###########################################################################################################

@app.route('/complaints_page')
def complaints_page():
    complaints = comp_db.get_complaints()
    return render_template('complaints.html', complaints=complaints)

############################################################################################################
@app.route('/search', methods=['GET'])
def search_products():
    search_query = request.args.get('query', '')
    # print(search_query)
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT product_id, product_name, description, category, size, price, image FROM products WHERE product_name ILIKE %s OR description ILIKE %s", 
                       (f"%{search_query}%", f"%{search_query}%"))
            product_data = cur.fetchall()
            # print(product_data)
        
        products = []
        for product in product_data:
            products.append({
                'pid': product[0],  # Match template's expected property name
                'pname': product[1], # Match template's expected property name
                'description': product[2],
                'category': product[3],
                'size': product[4],
                'price': product[5],
                'image': product[6]  # Keep the raw image data for your existing serve_product_image function
            })

        # print(products)
        
        return render_template('products.html', products=products, search_query=search_query)
        
    except Exception as e:
        print(f"Error searching products: {str(e)}")
        flash(f"An error occurred while searching for products: {str(e)}", "danger")
        return render_template('products.html', products=[], search_query=search_query)

##########################################################################################################################################
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()
    brand = request.args.get("brand")
    category = request.args.get("category")
    price_min = request.args.get("price_min", type=float)
    price_max = request.args.get("price_max", type=float)
    page = int(request.args.get("page", 1))  
    results_per_page = 10  

    if not query:
        return jsonify({"error": "Search query is required"}), 400

    corrected_query = correct_search_query(query)
    did_you_mean = corrected_query if corrected_query.lower() != query.lower() else None

    query_vector = tfidf_vectorizer.transform([corrected_query])
    cosine_similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    df["similarity"] = cosine_similarities
    search_results = df.sort_values(by="similarity", ascending=False)

    # Apply filters
    if brand:
        search_results = search_results[search_results["Brand"].str.contains(brand, case=False, na=False)]
    if category:
        search_results = search_results[search_results["Category"].str.contains(category, case=False, na=False)]
    if price_min is not None:
        search_results = search_results[search_results["Price"] >= price_min]
    if price_max is not None:
        search_results = search_results[search_results["Price"] <= price_max]

    # Remove results with `similarity = 0.0`
    search_results = search_results[search_results["similarity"] > 0.0]

    # Handle case where no search results exist
    if search_results.empty:
        return jsonify({
            "query": query,
            "corrected_query": did_you_mean,
            "results": [],
            "total_results": 0,
            "total_pages": 0
        })

    # Encode categorical features before model inference
    for column in ["Brand", "Category", "Color", "Gender", "Size"]:
        if column in search_results.columns and column in label_encoders:
            le = label_encoders[column]
            search_results[column] = search_results[column].apply(lambda x: le.transform([x])[0] if x in le.classes_ else 0)

    # Ensure all required features exist
    feature_cols = ["Brand", "Category", "Color", "Gender", "Size", "Price"]
    all_features = feature_cols + tfidf_feature_names
    for col in all_features:
        if col not in search_results.columns:
            search_results[col] = 0  # Add missing features as 0

    # Apply Gradient Boosting Model
    search_results["gb_score"] = gb_model.predict_proba(search_results[all_features])[:, 1]

    # Final ranking: Gradient Boosting (85%) + TF-IDF Similarity (15%)
    search_results["final_score"] = (0.85 * search_results["gb_score"]) + (0.15 * search_results["similarity"])
    search_results = search_results.sort_values(by="final_score", ascending=False)

    # **Correct Pagination**
    start_idx = (page - 1) * results_per_page
    end_idx = start_idx + results_per_page
    paginated_results = search_results.iloc[start_idx:end_idx]

    return jsonify({
        "query": query,
        "corrected_query": did_you_mean,
        "page": page,
        "results": paginated_results[["Product Name", "Brand", "Category", "Price", "similarity"]].to_dict(orient="records"),
        "total_results": len(search_results),
        "total_pages": (len(search_results) // results_per_page) + 1
    })

##############################################    cross sell and up sell ##############################################
@app.route('/product/<int:product_id>')
def product_view(product_id):
    if product_id not in products:
        return redirect(url_for('home'))
    
    product = products[product_id]
    return render_template('product_view.html', 
                           product=product, 
                           upsell_products=upsell_products, 
                           related_products=related_products)

@app.route('/uviewproduct/<int:product_id>')
def uviewproduct(product_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Fetch the specific product by its ID
            cur.execute("""
                SELECT product_id, product_name, description, category, size, price, image 
                FROM products 
                WHERE product_id = %s
            """, (product_id,))
            product_data = cur.fetchone()
            
            if not product_data:
                return render_template('error.html', message="Product not found"), 404
            
            # Create a modified product tuple with the correct image path format
            product = list(product_data)
            product[6] = f"product_{product_data[0]}.jpg"  # Make image path consistent with home page
            product = tuple(product)
            
            # Check if user is authenticated
            user_authenticated = 'user_id' in session
            
            # Use ProductRecommendations class to get dynamic product recommendations
            product_recommender = ProductRecommendations()
            
            # Get upsell products (premium options in same category)
            upsell_products = product_recommender.get_upsell_products(
            product_id=product_data[0],
            category=product_data[3], 
            product_name=product_data[1],  # Pass product_name
            price=product_data[5], 
            limit=4
            )
            
            # Get cross-sell products (complementary products from different categories)
            cross_sell_products = product_recommender.get_cross_sell_products(
            product_name=product_data[1],  
            description=product_data[2],   
            product_id=product_data[0],
            limit=4
            )   
            
            return render_template(
                'viewproduct.html', 
                product=product,
                user_authenticated=user_authenticated,
                upsell_products=upsell_products,
                cross_sell_products=cross_sell_products
            )
            
    except Exception as e:
        print(f"Error in view_product: {e}")
        return "An error occurred while fetching product details", 500

##################################################### cart ############################################# 

@app.route('/cart/add', methods=['POST'])
def add_to_cart_post():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to add items to your cart', 'warning')
        return redirect(url_for('login'))
    
    # Get form data
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    # Validate input
    if not product_id:
        flash('Invalid product', 'danger')
        return redirect(request.referrer or url_for('products.browse'))
    
    # Add item to cart
    cart = cart_db()
    if cart.add_to_cart(session['user_id'], product_id, quantity):
        flash('Item added to cart successfully', 'success')
    else:
        flash('Failed to add item to cart', 'danger')
    
    # Redirect back to the referring page or to the product listing
    return redirect(request.referrer or url_for('products.browse'))

@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to add items to your cart', 'warning')
        return redirect(url_for('login'))
    
    # Get quantity from form data (default to 1 if not provided)
    quantity = int(request.form.get('quantity', 1))
    
    # Add item to cart
    cart = cart_db()
    if cart.add_to_cart(session['user_id'], product_id, quantity):
        flash('Item added to cart successfully', 'success')
    else:
        flash('Failed to add item to cart', 'danger')
    
    # Redirect back to the referring page or to the cart page
    return redirect(request.referrer or url_for('view_cart'))

@app.route('/cart/update', methods=['POST'])
def cart_update_quantity():
    if 'user_id' not in session:
        flash('Please login to update your cart', 'warning')
        return redirect(url_for('login'))
    
    # Get form data
    item_id = request.form.get('item_id')
    quantity = int(request.form.get('quantity', 1))
    
    # Update quantity in database
    cart = cart_db()
    if cart.update_item_quantity(session['user_id'], item_id, quantity):
        flash('Cart updated successfully', 'success')
    else:
        flash('Failed to update cart', 'danger')
    
    return redirect(url_for('cart'))  # This is probably what's causing the error

@app.route('/cart')
def cart():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to view your cart', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cart = cart_db()
    
    # Get cart items for the user
    cart_items = cart.get_cart_items(user_id)
    
    # Process image data for display in HTML
    processed_items = []
    for item in cart_items:
        if item[2] is not None:  # If image exists
            # Convert binary data to base64 for HTML display
            encoded_image = base64.b64encode(item[2]).decode('utf-8')
            # Create a new tuple with the base64 image
            processed_item = (item[0], item[1], encoded_image, item[3], item[4], item[5])
        else:
            processed_item = item
        processed_items.append(processed_item)
    
    # Calculate totals
    subtotal = sum(item[5] for item in cart_items) if cart_items else 0
    
    # Calculate shipping (free for orders over 1000, otherwise 100)
    shipping = 0 if subtotal >= 1000 else 100
    
    # Calculate total
    total = subtotal + shipping
    
    return render_template('cart.html',
                          cart_items=processed_items,  # Use processed items
                          subtotal=subtotal,
                          shipping=shipping,
                          total=total)

@app.route('/cart/remove', methods=['POST'])
def cart_remove_item():
    if 'user_id' not in session:
        flash('Please login to remove items from your cart', 'warning')
        return redirect(url_for('login'))
    
    # Get form data
    item_id = request.form.get('item_id')
    
    # Remove item from database
    cart = cart_db()
    if cart.remove_item(session['user_id'], item_id):
        flash('Item removed from cart', 'success')
    else:
        flash('Failed to remove item from cart', 'danger')
    
    return redirect(url_for('cart'))  # Updated to use the renamed function

@app.route('/cart/clear', methods=['POST'])
def cart_clear():
    if 'user_id' not in session:
        flash('Please login to update your cart', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Clear the cart in your database
    cart = cart_db()
    success, message = cart.clear_cart(user_id)
    
    if success:
        flash('Cart cleared successfully', 'success')
    else:
        flash(f'Error clearing cart: {message}', 'danger')
    
    return redirect(url_for('cart'))  

#####################################################################################



#####################################################################################
@app.route('/product/<int:product_id>')
def view_product(product_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Fetch product details
            cur.execute("""
                SELECT product_id, product_name, description, category, size, price, image 
                FROM products 
                WHERE product_id = %s
            """, (product_id,))
            
            product = cur.fetchone()
            if not product:
                flash('Product not found', 'error')
                return redirect(url_for('home'))
            
            # Convert the fetched tuple to a dictionary
            product_dict = {
                'product_id': product[0], 
                'product_name': product[1],
                'description': product[2],
                'category': product[3],
                'size': product[4],
                'price': product[5],
                'image_url': f"/product_images/{product[0]}" if product[6] else "/static/images/default_product.jpg"
            }

            # Get cross-sell and upsell products using ProductRecommendations class
            recommendations = ProductRecommendations()
            cross_sell_products = recommendations.get_cross_sell_products(product_dict['pid'], product_dict['category'])
            upsell_products = recommendations.get_upsell_products(product_dict['pid'], product_dict['category'], product_dict['price'])

            # If fewer than 3 upsell products, fetch similar products
            if len(upsell_products) < 3:
                cur.execute("""
                    SELECT product_id, product_name, description, category, size, price, image
                    FROM products 
                    WHERE category = %s AND product_id != %s
                    LIMIT 3
                """, (product_dict['category'], product_dict['pid']))
                
                similar_products = []
                for p in cur.fetchall():
                    similar_products.append({
                    {
                        'product_id': product[0],  # Changed from 'pid'
                        'product_name': product[1],  # Changed from 'pname'
                        'description': product[2],
                        'category': product[3],
                        'size': product[4],
                        'price': product[5],
                        'image_url': f"/static/images/{product[0]}.jpg" if product[6] else "/static/images/default_product.jpg"
                    }
                    })

                # Fill remaining upsell slots with similar products
                for product in similar_products:
                    if len(upsell_products) >= 3:
                        break
                    if product['pid'] not in [p['pid'] for p in upsell_products]:
                        upsell_products.append(product)

            return render_template('viewproduct.html', 
                                   product=product_dict,
                                   cross_sell_products=cross_sell_products,
                                   upsell_products=upsell_products)

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('home'))
    
###############################################################################################

@app.route('/cart_checkout', methods=['GET', 'POST'])
def cart_checkout():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to continue to checkout', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Fetch all cart items for the user - note the CHANGE here
        cur.execute("""
            SELECT 
                p.product_id, 
                p.product_name, 
                p.size, 
                c.quantity, 
                p.price, 
                p.price * c.quantity as total_price,
                p.image
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.customer_id = %s  
        """, (user_id,))
        cart_items = cur.fetchall()
        
        if not cart_items:
            flash('Your cart is empty', 'warning')
            return redirect(url_for('home'))
        
        # Fetch customer details
        cur.execute("""
            SELECT customer_name, address, landmark, city, state, pincode, phone_number
            FROM customer
            WHERE user_id = %s
        """, (user_id,))
        customer_data = cur.fetchone()
    
    # Process cart items
    processed_items = []
    subtotal = 0
    for item in cart_items:
        # Convert image to base64 if exists
        image_data = None
        if item[6] is not None:
            try:
                import base64
                image_bytes = bytes(item[6])
                image_data = base64.b64encode(image_bytes).decode('utf-8')
            except Exception as e:
                print(f"Error converting image: {e}")
        
        processed_item = {
            'id': item[0],
            'name': item[1],
            'size': item[2],
            'quantity': item[3],
            'price': item[4],
            'total_price': item[5],
            'image': image_data
        }
        processed_items.append(processed_item)
        subtotal += item[5]
    
    # Calculate shipping
    shipping = 0 if subtotal >= 1000 else 100
    total = subtotal + shipping
    
    # Prepare customer data
    customer = None
    if customer_data:
        customer = {
            'name': customer_data[0],
            'street': customer_data[1],
            'landmark': customer_data[2] if customer_data[2] else '',
            'city': customer_data[3],
            'state': customer_data[4],
            'pincode': customer_data[5],
            'phone': customer_data[6]
        }
    
    return render_template('checkout.html',
                           products=processed_items,
                           subtotal=subtotal,
                           shipping=shipping,
                           total=total,
                           customer=customer)
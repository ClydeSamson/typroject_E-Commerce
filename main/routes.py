from flask import render_template, flash, redirect, url_for,request,jsonify,session, Response
from main import app,ALLOWED_EXTENSIONS,db
from main.forms import LoginForm,SignupForm,ProductForm
from datetime import datetime, timedelta
from .models import logclass,add_product_db,get_db_connection,comp_db
import os
from werkzeug.utils import secure_filename

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
    if 'user_id' in session:
        return redirect(url_for('home'))
        
    form = LoginForm()
    if form.validate_on_submit():
        db = logclass()
        success, message = db.verify_login(form.email.data, form.password.data)
        
        if success:
            session['user_id'] = message  
            session['email'] = form.email.data
            if form.remember.data:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash(f'Login failed: {message}', 'danger')
    
    return render_template('login.html', title='Login Page', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))
#########################################################################################################    

@app.route('/viewproduct/<int:product_id>')
def viewproduct(product_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Fetch product details
            cur.execute("""
                SELECT product_id, product_name, description, category, size, price, image 
                FROM products 
                WHERE product_id = %s
            """, (product_id,))
            
            product_data = cur.fetchone()
            
            if not product_data:
                return "Product not found", 404
            
            # Create product dictionary matching template variables
            product = {
                'title': product_data[1],  # product_name
                'description': product_data[2],
                'image_url': f"/product_images/{product_data[0]}" if product_data[6] else "/static/images/default_product.jpg",
                'price': product_data[5],
                'original_price': round(product_data[5] * 1.2, 2),  # Example calculation for original price
                'discount_percent': 20,  # Example discount percentage
                'rating': 4.5,  # Example rating
                'review_count': 24,  # Example review count
                'features': [
                    f"Category: {product_data[3]}",
                    f"Size: {product_data[4]}",
                    "High-quality material",
                    "Durable construction"
                ]
            }
            
            # Fetch related products for upsell and cross-sell
            cur.execute("""
                SELECT product_id, product_name, description, price, image
                FROM products 
                WHERE category = %s AND product_id != %s
                LIMIT 4
            """, (product_data[3], product_id))
            
            related_products = []
            for p in cur.fetchall():
                related_products.append({
                    'title': p[1],
                    'description': p[2][:50] + "..." if len(p[2]) > 50 else p[2],
                    'price': p[3],
                    'image_url': f"/product_images/{p[0]}" if p[4] else "/static/images/default_product.jpg"
                })
            
            return render_template(
                'viewproduct.html', 
                product=product, 
                upsell_products=related_products[:2], 
                cross_sell_products=related_products[2:] if len(related_products) > 2 else related_products
            )
            
    except Exception as e:
        print(f"Error in viewproduct: {e}")
        return "An error occurred while fetching product details", 500

@app.route('/product_images/<int:product_id>')
def product_images(product_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT image FROM products WHERE product_id = %s", (product_id,))
            image_data = cur.fetchone()
            
            if image_data and image_data[0]:
                return Response(image_data[0], mimetype='image/jpeg')
            else:
                return redirect('/static/images/default_product.jpg')
    except Exception as e:
        print(f"Error serving product image: {e}")
        return redirect('/static/images/default_product.jpg')

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

@app.route('/contact', methods=['POST'])
def contact():
    # API endpoint for AJAX form submission
    if request.is_json:
        data = request.get_json()
        
        # Process the form data
        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject')
        message = data.get('message')
        
        
        
        return jsonify({"message": f"Thank you, {name}! Your message has been received."})
    
    return jsonify({"message": "Invalid request"}), 400

@app.route('/checkout')
def checkout():
    # Define sample product data or retrieve from cart/database
    product = {
        'name': 'Sample Product',
        'size': 'M',
        'seller': 'Urban Style',
        'price': 999.00,
        'discount': 10,
        'platform_fee': 20.00
    }
    
    # Calculate total and savings
    total = product['price'] + product['platform_fee']
    savings = (product['price'] * product['discount'] / 100)
    
    # Define expiry time for payment
    expiry_time = '15:00 minutes'
    
    return render_template('checkout.html', 
                          product=product, 
                          total=total, 
                          savings=savings, 
                          expiry_time=expiry_time)

# @app.route('/save_address', methods=['POST'])
# def save_address():
#     address_data = request.json
#     # Here you would typically save this to a database
#     # For now, we'll just return it to confirm receipt
#     return jsonify({
#         'status': 'success',
#         'address': address_data
#     })

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

# @app.route('/dashboard/update_inventory', methods=['GET'])
# def update_inventory():
#     """Route to render the update inventory page"""
#     try:
#         with get_db_connection() as conn:
#             cur = conn.cursor()
#             cur.execute("SELECT product_id, product_name, category, size, price, stock FROM products")
#             products_data = cur.fetchall()
            
#             products = []
#             for product in products_data:
#                 image_path = f"product_{product[0]}.jpg"
                
#                 products.append({
#                     'id': product[0],
#                     'name': product[1],
#                     'category': product[2],
#                     'size': product[3],
#                     'price': product[4],
#                     'stock': product[5] if len(product) > 5 else 0,  # Handle case if stock column doesn't exist
#                     'image': image_path
#                 })
                
#             return render_template('update_inventory.html', products=products)
#     except Exception as e:
#         print(f"Error fetching products for inventory update: {str(e)}")
#         flash('Error loading products. Please try again later.', 'danger')
#         return render_template('update_inventory.html', products=[])

# @app.route('/api/update_inventory', methods=['POST'])
# def api_update_inventory():
#     """API endpoint to handle inventory updates"""
#     try:
#         data = request.json
#         updated_products = data.get('products', [])
        
#         with get_db_connection() as conn:
#             cur = conn.cursor()
            
#             for product in updated_products:
#                 # Check if the stock column exists in the products table
#                 cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='products' AND column_name='stock'")
#                 stock_column_exists = cur.fetchone() is not None
                
#                 if not stock_column_exists:
#                     # Add stock column if it doesn't exist
#                     cur.execute("ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 0")
#                     conn.commit()
                
#                 # Update the product price and stock
#                 cur.execute(
#                     "UPDATE products SET price = %s, stock = %s WHERE product_id = %s",
#                     (product['price'], product['stock'], product['id'])
#                 )
            
#             conn.commit()
            
#         return jsonify({
#             'success': True,
#             'message': 'Inventory updated successfully'
#         })
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'message': f'Error updating inventory: {str(e)}'
#         }), 500
    
# @app.route('/dashboard/orders_page', methods=['GET', 'POST'])
# def orders_page():
#     return render_template('orders_page.html')

@app.route('/search', methods=['GET'])
def search_products():
    search_query = request.args.get('query', '')
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT product_id, product_name, description, category, size, price, image FROM products WHERE product_name ILIKE %s OR description ILIKE %s", 
                       (f"%{search_query}%", f"%{search_query}%"))
            product_data = cur.fetchall()
        
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
        
        return render_template('products.html', products=products, search_query=search_query)
        
    except Exception as e:
        print(f"Error searching products: {str(e)}")
        flash(f"An error occurred while searching for products: {str(e)}", "danger")
        return render_template('products.html', products=[], search_query=search_query)


products = {
    1: {
        'id': 1,
        'title': 'Premium Wireless Headphones with Noise Cancellation',
        'price': 149.99,
        'original_price': 199.99,
        'discount': 25,
        'rating': 4.2,
        'reviews': 128,
        'description': 'Experience crystal-clear sound with our premium wireless headphones featuring advanced noise cancellation technology, 30-hour battery life, and ultra-comfortable design.',
        'image': '/static/uploads/jeans.jpg',
        'features': [
            'High-definition sound quality with 40mm dynamic drivers',
            'Active Noise Cancellation technology',
            '30-hour battery life with quick-charge capability',
            'Bluetooth 5.0 with multipoint connection',
            'Built-in microphone with echo cancellation',
            'Comfortable memory foam ear cushions',
            'Foldable design for easy storage and travel',
            'Touch controls for volume, track selection, and calls',
            'Voice assistant compatibility (Siri, Google Assistant, Alexa)'
        ]
    }
}

# Sample upsell products
upsell_products = [
    {
        'id': 2,
        'title': 'Premium Wireless Headphones Pro (2025 Edition)',
        'price': 249.99,
        'description': 'Upgraded version with Hi-Res Audio certification, 40-hour battery life, and premium materials.',
        'image': '/api/placeholder/300/300'
    },
    {
        'id': 3,
        'title': 'Premium True Wireless Earbuds with ANC',
        'price': 179.99,
        'description': 'Same great sound quality in a compact, truly wireless design with active noise cancellation.',
        'image': '/api/placeholder/300/300'
    }
]

# Sample related products
related_products = [
    {
        'id': 4,
        'title': 'Aluminum Headphone Stand',
        'price': 29.99,
        'description': 'Elegant aluminum stand to display and store your headphones.',
        'image': '/api/placeholder/300/300'
    },
    {
        'id': 5,
        'title': 'Premium Hard Shell Travel Case',
        'price': 24.99,
        'description': 'Protective case for your headphones while traveling or on the go.',
        'image': '/api/placeholder/300/300'
    },
    {
        'id': 6,
        'title': 'Memory Foam Replacement Ear Pads',
        'price': 19.99,
        'description': 'Extra comfortable replacement ear pads for extended listening.',
        'image': '/api/placeholder/300/300'
    },
    {
        'id': 7,
        'title': 'Premium 3.5mm Audio Cable',
        'price': 14.99,
        'description': 'High-quality braided audio cable for wired connection.',
        'image': '/api/placeholder/300/300'
    }
]
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
        # Connect to the database
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Fetch the specific product by its ID
            cur.execute("""
                SELECT product_id, product_name, description, category, size, price, image 
                FROM products 
                WHERE product_id = %s
            """, (product_id,))
            product = cur.fetchone()
            
            if not product:
                # Handle case where product doesn't exist
                return render_template('error.html', message="Product not found"), 404
            
            # Fetch related products in the same category for recommendations
            cur.execute("""
                SELECT product_id, product_name, description, category, size, price, image 
                FROM products 
                WHERE category = %s AND product_id != %s 
                LIMIT 4
            """, (product[3], product_id))
            related_products = cur.fetchall()
            
            # Fetch products for cross-sell (different category)
            cur.execute("""
                SELECT product_id, product_name, description, category, size, price, image 
                FROM products 
                WHERE category != %s 
                LIMIT 2
            """, (product[3],))
            cross_sell_products = cur.fetchall()
            
        # Handle binary image data if needed
        # If your image is stored as binary data, you'll need additional logic here
        # or a separate route to serve the images
            
        # Render the template with all product data
        return render_template('viewproduct.html', 
                              product=product, 
                              related_products=related_products,
                              cross_sell_products=cross_sell_products)
                              
    except Exception as e:
        # Log the error and return an error page
        print(f"Error displaying product: {str(e)}")
        return render_template('error.html', message="An error occurred while loading the product"), 500


@app.route('/cart')
def cart_view():
    cart_items = []
    total = 0
    
    if 'cart' in session:
        for product_id, quantity in session['cart'].items():
            product_id = int(product_id)
            if product_id in products:
                product = products[product_id]
                item_total = product['price'] * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total': item_total
                })
                total += item_total
    
    return render_template('cart.html', cart_items=cart_items, total=total)

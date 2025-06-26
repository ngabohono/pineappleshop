from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Product, CartItem, Order, OrderItem, Category,User,SearchLog,Rating
from . import db
from datetime import datetime
import pandas as pd
import os
from werkzeug.utils import secure_filename
from flask import current_app
import re
from flask_mail import Message
from . import mail  # Adjust the import according to your app structure
from flask import request, jsonify
from sqlalchemy import or_

main = Blueprint('main', __name__)


@main.context_processor
def inject_cart_quantity():
    categories = Category.query.order_by(Category.name).all()
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        quantity = sum(item.quantity for item in cart_items)
        return dict(cart_quantity=quantity,categories=categories)
    return dict(cart_quantity=0,categories=categories)

def load_products():
    products = os.path.join(current_app.root_path, 'static', 'dataset', 'products.csv')
    return pd.read_csv(products)

def load_search_logs():
    recommendations = os.path.join(current_app.root_path, 'static', 'dataset', 'search_logs.csv')
    return pd.read_csv(recommendations)

def slugify(text):
    # Lowercase the text
    text = text.lower()
    # Remove non-word characters (excluding hyphen and space)
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def get_trending_recommendations(limit=5):
    trending_terms = SearchLog.query.order_by(SearchLog.count.desc()).limit(limit).all()
    recommendations = []
    seen_product_ids = set()

    for term in trending_terms:
        matched = Product.query.filter(Product.name.ilike(f"%{term.term}%")).first()
        if matched and matched.id not in seen_product_ids:
            recommendations.append(matched)
            seen_product_ids.add(matched.id)

    return recommendations



@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'customer':
        total_orders = Order.query.filter_by(user_id=current_user.id).count()
        return render_template('dashboard.html', total_orders=total_orders)
    else:
        # For both admin and seller roles
        if current_user.role == 'admin':
            # Admins see all products and stats
            total_users = User.query.count()
            total_products = Product.query.count()
            total_orders = Order.query.count()
            total_categories = Category.query.count()
            my_products = Product.query.all()  # Admin sees all products
        else:
            # Non-admin users (sellers) only see their own products
            total_users = 1  # Just themselves
            total_products = Product.query.filter_by(user_id=current_user.id).count()
            # Count orders that contain their products
            my_product_ids = db.session.query(Product.id).filter_by(user_id=current_user.id).all()
            my_product_ids = [pid[0] for pid in my_product_ids]
            
            if my_product_ids:
                total_orders = db.session.query(Order.id).join(OrderItem).filter(
                    OrderItem.product_id.in_(my_product_ids)
                ).distinct().count()
            else:
                total_orders = 0
            
            total_categories = db.session.query(Category.id).join(Product).filter(
                Product.user_id == current_user.id
            ).distinct().count()
            
            my_products = Product.query.filter_by(user_id=current_user.id).all()
        
        my_total_orders = Order.query.filter_by(user_id=current_user.id).count()
        
        return render_template(
            'admin_dashboard.html',
            total_users=total_users,
            total_products=total_products,
            total_orders=total_orders,
            total_categories=total_categories,
            my_total_orders=my_total_orders,
            my_products=my_products,  # Add this to pass products to template
            is_admin=(current_user.role == 'admin')  # Add this flag
        )

@main.route('/shop/category/<category_name>')
def searchcategory(category_name):
    
    search = SearchLog.query.filter_by(term=category_name).first()
    if search:
        search.count += 1
    else:
        search = SearchLog(term=category_name)
        db.session.add(search)
    db.session.commit()
    
    category = Category.query.filter_by(slug=category_name).first()
    if not category:
        # No such category found, return empty or 404
        results = []
    else:
        results = Product.query.filter_by(category_id=category.id).all()

    return render_template('search.html', results=results, query=category_name)
  

@main.route('/search')
def search():
    query = request.args.get('q', '')
    
    search = SearchLog.query.filter_by(term=query).first()
    if search:
        search.count += 1
    else:
        search = SearchLog(term=query)
        db.session.add(search)
    db.session.commit()
    
    # Search for products where the name contains the query string (case-insensitive)
    results = Product.query.filter(Product.name.ilike(f"%{query}%")).all()

    return render_template('search.html', query=query, results=results)

# @main.route('/')
# @main.route('/home')
# def home():
#     recommendations = get_trending_recommendations()
#     products = Product.query.all()
#     return render_template('index.html', products=products,recommendations=recommendations)


@main.route('/')
@main.route('/home')
def home():
    recommendations = get_trending_recommendations()

    # Get IDs of recommended products
    recommended_ids = [p.id for p in recommendations]

    # Query all products excluding the recommended ones
    products = Product.query.filter(~Product.id.in_(recommended_ids)).limit(20).all()

    return render_template('index.html', products=products, recommendations=recommendations)



# @main.route('/')
# def index():
#     products = Product.query.all()
#     return render_template('index.html', products=products)

@main.route('/product/<product_id>')
def product(product_id):
    # product = Product.query.get_or_404(product_id)
    if product_id.isdigit():
        # fetch by id (int)
        # product = Product.query.get(int(product_id))
        product = Product.query.get_or_404(product_id)
        if product.views is None:
            product.views = 1
        else:
            product.views += 1
        db.session.commit()
    else:
        # fetch by slug (string)
        product = Product.query.filter_by(slug=product_id).first()
        if product.views is None:
            product.views = 1
        else:
            product.views += 1
        db.session.commit()
    
    recommendations = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id  # exclude the current product
    ).limit(4).all()
    return render_template('product.html', product=product, recommendations=recommendations)

# @main.route('/cart')
# @login_required
# def cart():
#     cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
#     total = sum(item.product.price * item.quantity for item in cart_items)
#     return render_template('cart.html', cart_items=cart_items, total=total)

@main.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    # Filter out items with deleted products
    valid_cart_items = [item for item in cart_items if item.product is not None]
    
    for item in cart_items:
        if item.product is None:
            db.session.delete(item)
    db.session.commit()


    total = sum(item.product.price * item.quantity for item in valid_cart_items)

    return render_template('cart.html', cart_items=valid_cart_items, total=total)

@main.route('/add-to-cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    cart_item = CartItem.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id
    ).first()

    # Check total cart quantity vs available stock
    if cart_item:
        if cart_item.quantity >= product.stock:
            flash(f'You cannot add more than {product.stock}, which is in the stock.', 'warning')
            return redirect(url_for('main.product_details', product_id=product_id))
        cart_item.quantity += 1
    else:
        if product.stock < 1:
            flash('This product is currently out of stock.', 'danger')
            return redirect(url_for('main.product_details', product_id=product_id))
        cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(cart_item)

    db.session.commit()
    flash('Item added to cart!', 'success')
    return redirect(url_for('main.product_details', product_id=product_id))



@main.route('/checkout')
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('checkout.html', total=total)


@main.route('/add-category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        category = Category(
            name=request.form['name'],
            slug = slugify(request.form['name']),
            description=request.form['description'],
        )
        db.session.add(category)
        db.session.commit()
        return redirect(url_for('main.categories'))
    return render_template('admin/add_category.html')

@main.route('/categories')
def categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@main.route('/edit/category/<int:id>', methods=['GET', 'POST'])
def edit_category(id):
    category = Category.query.get_or_404(id)
    if request.method == 'POST':
        category.name = request.form['name']
        category.description = request.form['description']
        db.session.commit()
        return redirect(url_for('main.categories'))
    return render_template('admin/edit_category.html', category=category)

@main.route('/delete/category/<int:id>')
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('main.categories'))


# Update the index route to show only user's products (unless admin)
@main.route('/all-products')
@login_required
def index():
    if current_user.role == 'admin':
        # Admins can see all products
        products = Product.query.all()
    else:
        # Regular users see only their own products
        products = Product.query.filter_by(user_id=current_user.id).all()
    
    
    # for product in products:
    #     ratings = product.ratings.all()
    #     product.average_rating = round(sum(r.stars for r in ratings), 1) if ratings else 0
    
    return render_template('admin/index.html', products=products)


# Update the add_product route to save the user_id
@main.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    categories = Category.query.all()
    if request.method == 'POST':
        name = request.form['name']
        slug = slugify(name)
        brief = request.form['brief']
        price = request.form['price']
        description = request.form['description']
        stock = request.form['stock']
        image_file = request.files['image']
        category_id = request.form.get('category_id')
        
        filename = None
        if image_file and image_file.filename:
            original_filename = secure_filename(image_file.filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            name_part, ext = os.path.splitext(original_filename)
            filename = f"{name_part}_{timestamp}{ext}"
            image_path = os.path.join(current_app.root_path, 'static/images', filename)
            image_file.save(image_path)

        new_product = Product(
            name=name,
            price=price,
            description=description,
            stock=stock,
            image=filename,
            slug=slug,
            brief=brief,
            category_id=int(category_id) if category_id else None,
            user_id=current_user.id  # Add this line to save the owner
        )
        db.session.add(new_product)
        db.session.commit()

        flash('Product added successfully!')
        return redirect(url_for('main.index'))

    return render_template('admin/add_product.html', categories=categories)


# Update the edit_product route with authorization
@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    # Check if user is authorized to edit this product
    if current_user.role != 'admin' and product.user_id != current_user.id:
        flash('You are not authorized to edit this product.', 'danger')
        return redirect(url_for('main.index'))
    
    categories = Category.query.all()
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = request.form['price']
        product.description = request.form['description']
        product.brief = request.form['brief']
        product.image = request.form['image']
        product.stock = request.form['stock']
        
        category_id = request.form.get('category_id')
        product.category_id = int(category_id) if category_id else None

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('main.index'))
    return render_template('admin/edit_product.html', product=product, categories=categories)


# Update the delete_product route with authorization
@main.route('/delete/<int:id>')
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    # Check if user is authorized to delete this product
    if current_user.role != 'admin' and product.user_id != current_user.id:
        flash('You are not authorized to delete this product.', 'danger')
        return redirect(url_for('main.index'))
    
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('main.index'))



@main.route('/product-details/<product_id>')
def product_details(product_id):    
    return redirect(url_for('main.product', product_id=product_id))

@main.route('/place_order', methods=['POST'])
@login_required
def place_order():
    name = request.form.get('name')
    address = request.form.get('address')

    if not name or not address:
        flash("Please fill out all fields.")
        return redirect(url_for('main.checkout'))

    # Fetch cart items for current user
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash("Your cart is empty.")
        return redirect(url_for('main.home'))

    # Create new order
    new_order = Order(customer_name=name, address=address, total_price=0, user_id=current_user.id)
    db.session.add(new_order)
    db.session.flush()  # To get the new_order.id before commit

    total = 0
    order_details = ""
    for item in cart_items:
        product = item.product
        if product:
            if item.quantity > product.stock:
                flash(f"Not enough stock for {product.name}. Available: {product.stock}")
                return redirect(url_for('main.checkout'))

            # Deduct stock
            product.stock -= item.quantity

            # Add order item
            subtotal = product.price * item.quantity
            total += subtotal
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=item.quantity,
                price=product.price
            )
            db.session.add(order_item)
            order_details += f"{product.name} (x{item.quantity}) - ${subtotal:.2f}\n"

    new_order.total_price = total
    db.session.commit()

    # Clear the cart
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    # ✉️ Send email
    try:
        msg = Message("New Order Placed",
                      recipients=[current_user.email]) 
        msg.body = f"""
            Hello {current_user.username},

            Thank you for your order!

            Order Summary:
            ---------------
            Name: {name}
            Address: {address}
            Total: RF{total:.2f}

            Items:
            {order_details}

            We'll notify you once your order is shipped.

            Best,
            Seller
            """
        mail.send(msg)
    except Exception as e:
        print("Failed to send email:", e)

    flash("Order placed successfully!")
    return redirect(url_for('main.home'))

@main.route('/clearcart')
@login_required
def clearcart():
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("Order placed successfully!")
    return redirect(url_for('main.home'))

@main.route('/orders')
@login_required
def view_orders():
    if current_user.role == 'admin':
        # Admins can see all orders
        orders = Order.query.order_by(Order.created_at.desc()).all()
        page_title = "All Orders"
        
    else:
        # Non-admin users (sellers) only see orders containing their products
        # First, get all product IDs owned by the current user
        user_product_ids = db.session.query(Product.id).filter_by(user_id=current_user.id).all()
        user_product_ids = [pid[0] for pid in user_product_ids]
        
        if user_product_ids:
            # Get orders that contain at least one of the user's products
            orders = Order.query.join(OrderItem).filter(
                OrderItem.product_id.in_(user_product_ids)
            ).distinct().order_by(Order.created_at.desc()).all()
            
            # For each order, we might want to highlight which items belong to this seller
            for order in orders:
                # Add a custom attribute to track seller's items in this order
                seller_items = [item for item in order.items if item.product_id in user_product_ids]
                order.seller_items = seller_items
                order.seller_revenue = sum(item.price * item.quantity for item in seller_items)
        else:
            # User has no products, so no orders to show
            orders = []
            
        page_title = "Orders for My Products"
    
    # Calculate some statistics
    total_orders = len(orders)
    total_revenue = sum(order.total_price for order in orders) if current_user.role == 'admin' else \
                   sum(getattr(order, 'seller_revenue', 0) for order in orders)
    
    return render_template('orders.html', 
                         orders=orders, 
                         page_title=page_title,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         is_admin=(current_user.role == 'admin'))


@main.route('/user/orders')
@login_required
def view_user_orders():
    # If you're building for admin, fetch all orders
    orders = Order.query.order_by(Order.created_at.desc()).filter_by(user_id=current_user.id).all()

    # If it's for a regular user, filter orders by user (if your model links user)
    return render_template('orders.html', orders=orders)

@main.route("/about-us")
def about():
    return render_template("about.html")

@main.route("/delivery-information")
def delivery():
    return render_template("delivery.html")

@main.route("/privacy-policy")
def privacy():
    return render_template("privacy.html")

@main.route("/who-we-are")
def who_we_are():
    return render_template("who_we_are.html")

@main.route("/our-services")
def our_services():
    return render_template("our_services.html")

@main.route("/contact-us", methods=["GET"])
def contact_us():
    return render_template("contact_us.html")

@main.route("/send-message", methods=["POST"])
def send_message():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    # You can add email-sending logic or save to a database here
    flash("Thanks for reaching out! We'll get back to you soon.")
    return redirect(url_for('main.contact_us'))

@main.route("/subscription", methods=["POST"])
def subscriptions():
    email = request.form['email']
    # Save email or send confirmation logic
    flash("Thanks for subscribing! You will get updates soon.")
    
    # Redirect back to the referring page
    return redirect(request.referrer or '/')



@main.route('/users')
def users():
    users = User.query.all()
    return render_template('auth/users.html', users=users)

@main.route('/edit/user/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        dob_str = request.form['DOB']
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()  # convert string to date object    

        user.username = request.form['username']
        user.email = request.form['email']
        user.first_name = request.form['first_name']        
        # user.role = request.form['role']
        if current_user.role == "admin" or current_user.email == "jcturisangait1996@gmail.com" or  current_user.email == "ngabohonorek@gmail.com":
            user.role = request.form['role']
        else:
            user.role = user.role  # Or skip entirely

        user.lastname = request.form['lastname']
        user.NID = request.form['NID']
        user.DOB = dob
        user.gender = request.form['gender']
        
        user.province = request.form['province']
        user.district = request.form['district']
        user.sector = request.form['sector']
        user.cell = request.form['cell']
        user.village = request.form['village']
        
        db.session.commit()
        return redirect(url_for('main.users'))
    return render_template('auth/edit_user.html', user=user)

@main.route('/delete/user/<int:id>')
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('main.users'))

@main.route('/show-dataset')
def show_dataset():
    products = load_products().head(50).to_dict(orient='records')  # Show first 50 products
    search_logs = load_search_logs().head(50).to_dict(orient='records')
    return render_template('show_dataset.html', products=products, search_logs=search_logs)

@main.route('/rate/<int:product_id>', methods=['POST'])
@login_required
def rate_product(product_id):
    try:
        stars = int(request.form.get('stars'))
        comment = request.form.get('comment', '').strip()
        
        # Validate stars range
        if not (1 <= stars <= 5):
            flash('Please select a rating between 1 and 5 stars.', 'error')
            return redirect(request.referrer or url_for('main.home'))

        # Check if the user already rated this product
        existing = Rating.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if existing:
            existing.stars = stars
            existing.comment = comment
            flash('Your rating has been updated!', 'success')
        else:
            rating = Rating(user_id=current_user.id, product_id=product_id, stars=stars, comment=comment)
            db.session.add(rating)
            flash('Your rating has been submitted!', 'success')

        db.session.commit()
        
    except ValueError:
        flash('Invalid rating value. Please try again.', 'error')
    except Exception as e:
        db.session.rollback()
        flash('Error submitting rating. Please try again.', 'error')

    # Redirect back to product details
    product = Product.query.get_or_404(product_id)
    slug_or_id = product.slug if product.slug is not None else product.id
    return redirect(url_for('main.product_details', product_id=slug_or_id))





@main.route('/live-search')
def live_search():
    """API endpoint for live search suggestions"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({'results': []})
        
        # Search in product name, description, and brief
        # Limit to 8 results for dropdown
        products = Product.query.filter(
            or_(
                Product.name.ilike(f'%{query}%'),
                Product.description.ilike(f'%{query}%'),
                Product.brief.ilike(f'%{query}%')
            )
        ).limit(8).all()
        
        # Convert products to JSON format
        results = []
        for product in products:
            results.append({
                'id': product.id,
                'slug': product.slug,
                'name': product.name,
                'price': float(product.price),
                'image': product.image,
                'average_rating': product.average_rating,
                'review_count': product.review_count,
                'brief': product.brief[:100] + '...' if product.brief and len(product.brief) > 100 else product.brief
            })
        
        return jsonify({'results': results})
        
    except Exception as e:
        print(f"Live search error: {e}")
        return jsonify({'results': [], 'error': 'Search temporarily unavailable'})


# Alternative with more advanced search features
@main.route('/live-search-advanced')
def live_search_advanced():
    """Advanced live search with relevance scoring"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({'results': []})
        
        # Search with different weights for relevance
        # Exact name matches get higher priority
        exact_matches = Product.query.filter(
            Product.name.ilike(f'{query}%')
        ).limit(3).all()
        
        # Then partial name matches
        partial_matches = Product.query.filter(
            Product.name.ilike(f'%{query}%')
        ).filter(
            ~Product.name.ilike(f'{query}%')  # Exclude exact matches
        ).limit(3).all()
        
        # Finally description matches
        description_matches = Product.query.filter(
            or_(
                Product.description.ilike(f'%{query}%'),
                Product.brief.ilike(f'%{query}%')
            )
        ).filter(
            ~Product.name.ilike(f'%{query}%')  # Exclude name matches
        ).limit(2).all()
        
        # Combine results with priority order
        all_products = exact_matches + partial_matches + description_matches
        
        # Remove duplicates while preserving order
        seen = set()
        unique_products = []
        for product in all_products:
            if product.id not in seen:
                seen.add(product.id)
                unique_products.append(product)
        
        # Convert to JSON
        results = []
        for product in unique_products[:8]:  # Limit to 8 results
            results.append({
                'id': product.id,
                'slug': product.slug,
                'name': product.name,
                'price': float(product.price),
                'image': product.image,
                'average_rating': product.average_rating,
                'review_count': product.review_count,
                'brief': product.brief[:100] + '...' if product.brief and len(product.brief) > 100 else product.brief,
                'stock': product.stock
            })
        
        return jsonify({'results': results})
        
    except Exception as e:
        print(f"Advanced live search error: {e}")
        return jsonify({'results': [], 'error': 'Search temporarily unavailable'})

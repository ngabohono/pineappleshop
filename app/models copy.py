from app import db  # Import db directly from app

from flask_login import UserMixin
from datetime import datetime
import pytz
from datetime import date

kigali_tz = pytz.timezone("Africa/Kigali")

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    lastname = db.Column(db.String(150), nullable=True)
    NID = db.Column(db.String(20), nullable=True)
    DOB = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    image = db.Column(db.String(150), nullable=True)
    role = db.Column(db.String(50), default='customer')
    cart_items = db.relationship('CartItem', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    
    # NEW ADDRESS COLUMNS - Add these lines
    province = db.Column(db.String(50), nullable=True)
    district = db.Column(db.String(50), nullable=True)
    sector = db.Column(db.String(50), nullable=True)
    cell = db.Column(db.String(50), nullable=True)
    village = db.Column(db.String(50), nullable=True)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    # Required for Flask-Login
    def get_id(self):
        return str(self.id)  # Convert to string as Flask-Login expects string IDs
    


# class Product(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     slug = db.Column(db.String(200), nullable=True)
#     price = db.Column(db.Float, nullable=False)
#     description = db.Column(db.Text, nullable=True)
#     brief = db.Column(db.String(250), nullable=True)
#     image = db.Column(db.String(100), nullable=True)
#     stock = db.Column(db.Integer, default=0)
#     views = db.Column(db.Integer, default=0) 
#     category_id = db.Column(db.Integer, db.ForeignKey('category.id', name='fk_product_category'), nullable=True)
#     ratings = db.relationship('Rating', back_populates='product', lazy='dynamic')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(200), nullable=True)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    brief = db.Column(db.String(250), nullable=True)
    image = db.Column(db.String(100), nullable=True)
    stock = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0) 
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', name='fk_product_category'), nullable=True)
    ratings = db.relationship('Rating', back_populates='product', lazy='dynamic')

    @property
    def average_rating(self):
        """Calculate average rating for this product"""
        ratings_list = list(self.ratings)  # Convert dynamic query to list
        if not ratings_list:
            return 0
        total_rating = sum(rating.stars for rating in ratings_list)
        return round(total_rating / len(ratings_list), 1)
    
    @property
    def review_count(self):
        """Get total number of ratings for this product"""
        return self.ratings.count()  # Use count() for dynamic relationship
    
    @property
    def rating_distribution(self):
        """Get distribution of ratings (1-5 stars)"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in self.ratings:
            if 1 <= rating.stars <= 5:
                distribution[rating.stars] += 1
        return distribution
    
    @property
    def has_ratings(self):
        """Check if product has any ratings"""
        return self.ratings.count() > 0

    
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)    
    slug = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    products = db.relationship('Product', backref='category', lazy=True)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    product = db.relationship('Product', backref='cart_items')
    
    
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Customer Information
    customer_name = db.Column(db.String(100), nullable=False)  # Keep for backward compatibility
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    # Address Information
    address = db.Column(db.String(500), nullable=False)  # Keep for backward compatibility
    province = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    sector = db.Column(db.String(50), nullable=False)
    cell = db.Column(db.String(50), nullable=True)
    village = db.Column(db.String(50), nullable=True)
    address_details = db.Column(db.Text, nullable=True)  # Detailed address/instructions
    
    # Order Information
    total_price = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False, default='cash_on_delivery')
    payment_status = db.Column(db.String(20), nullable=False, default='pending')  # pending, paid, failed
    order_status = db.Column(db.String(20), nullable=False, default='processing')  # processing, shipped, delivered, cancelled
    order_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(kigali_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(kigali_tz), onupdate=lambda: datetime.now(kigali_tz))
    shipped_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_user_order'), nullable=True)
    
    # Properties for convenience
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_address(self):
        """Generate full address string"""
        address_parts = [
            self.address_details,
            self.village,
            self.cell,
            self.sector,
            self.district,
            self.province
        ]
        return ", ".join([part for part in address_parts if part])
    
    @property
    def items_count(self):
        """Total number of items in order"""
        return sum(item.quantity for item in self.items)
    
    @property
    def status_color(self):
        """Get color class for order status"""
        status_colors = {
            'processing': 'yellow',
            'shipped': 'blue',
            'delivered': 'green',
            'cancelled': 'red'
        }
        return status_colors.get(self.order_status, 'gray')
    
    def __repr__(self):
        return f'<Order {self.id}: {self.full_name} - RF{self.total_price}>'


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price at time of order
    
    # Additional item information
    product_name = db.Column(db.String(200), nullable=False)  # Store product name at time of order
    product_image = db.Column(db.String(200), nullable=True)  # Store image path at time of order
    
    # Relationships
    product = db.relationship('Product')
    
    @property
    def total_price(self):
        """Total price for this item (price × quantity)"""
        return self.price * self.quantity
    
    def __repr__(self):
        return f'<OrderItem {self.id}: {self.product_name} x{self.quantity}>'


# Optional: Order Status History for tracking changes
class OrderStatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(kigali_tz))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Admin who made the change
    
    # Relationships
    order = db.relationship('Order', backref='status_history')
    user = db.relationship('User', backref='order_status_changes')
    
    def __repr__(self):
        return f'<OrderStatusHistory {self.id}: Order {self.order_id} -> {self.status}>'

class SearchLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(100), nullable=False)
    count = db.Column(db.Integer, default=1)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stars = db.Column(db.Integer, nullable=False)  # Range from 1 to 5
    comment = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    user = db.relationship('User', backref='ratings')
    product = db.relationship('Product', back_populates='ratings')
    
# User loader function must be after User model is defined
from app import login_manager  # Import login_manager from the app directly
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

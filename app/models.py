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
    ratings = db.relationship('Rating', back_populates='product', lazy='dynamic', cascade='all, delete-orphan')

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
    customer_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(kigali_tz))
    items = db.relationship('OrderItem', backref='order', lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_user_order'), nullable=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product')

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

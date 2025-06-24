from app import create_app, db
from app.models import Product  # Import Product model

# Create the Flask app instance
app = create_app()

# Use app context to run database queries
with app.app_context():
    # Query all products from the Product table
    products = Product.query.all()
    
    # Print out the products
    for product in products:
        print(f"Product: {product.name}, Price: {product.price}")

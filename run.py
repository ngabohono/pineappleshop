from app import create_app, db
import os
app = create_app()

# Create database tables within application context
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # app.run(debug=True)
    port = int(os.environ.get('PORT', 5000))  # Use Render's PORT
    app.run(host='0.0.0.0', port=port, debug=True)

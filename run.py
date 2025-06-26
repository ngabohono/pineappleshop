from app import create_app, db
import os
app = create_app()

# Create database tables within application context
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # app.run(debug=True)
    port = int(os.environ.get('PORT', 5000))  # Use Render's PORT
<<<<<<< HEAD
    app.run(host='0.0.0.0', port=port, debug=True)
=======
    app.run(host='0.0.0.0', port=port, debug=True)
>>>>>>> dea9c98ccc4156ecaff25de8bd769fe2b886a50c

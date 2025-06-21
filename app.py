from web_app import app, db
import web_app.models
import web_app.views
import os


print("from app.py")

# Ensure the upload folder exists (config a path from __init__.py)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

print("UPLOAD_FOLDER =", app.config['UPLOAD_FOLDER'])


if __name__ == '__main__':
    with app.app_context():
        #db.drop_all()        # Optional: Use only for resetting the DB
        db.create_all()        # Create tables if they don’t exist
    app.run(debug=True)

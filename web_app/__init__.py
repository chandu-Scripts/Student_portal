# web_app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from config_package.config import Config

# 🔧 Initialize extensions (no app bound yet)
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()

# 📦 Create Flask app instance
app = Flask(__name__)
app.config.from_object(Config)  # Load config from config_package/config.py

# 🔗 Bind extensions to app
db.init_app(app)
mail.init_app(app)
login_manager.init_app(app)

# 🔐 Set the login view (for @login_required redirects)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'  # ✅ extra security (optional)

# 🌐 Print upload folder path for debug
print("path", app.config['UPLOAD_FOLDER'])

# 👇 Import views after app is fully set up to avoid circular imports
from web_app import views

# 📤 Make these accessible from outside (like in models.py)
__all__ = ['app', 'db', 'mail', 'login_manager']

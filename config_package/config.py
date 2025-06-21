import os

print("from config")  # Optional debug print

class Config:
    # ✅ MySQL Database Configuration
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@localhost/ferilion_portal'  # Update credentials if needed
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ✅ Flask Secret Key (used for sessions, flash messages, Flask-Login)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_super_secret_key_1234567890'

    # ✅ Flask-Mail Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'tcs9122119@gmail.com'  # Your email
    MAIL_PASSWORD = 'lqpbqvtcgyhlaqag'      # App password (no spaces)
    MAIL_DEFAULT_SENDER = 'tcs9122119@gmail.com'

    # ✅ Base Directory for building paths
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # ✅ Video Upload Configuration
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'web_app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2 GB
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

    # ✅ Notes Upload Configuration
    NOTES_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'web_app', 'static', 'notes')
    ALLOWED_NOTE_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx'}

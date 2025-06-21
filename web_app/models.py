from web_app import db, login_manager
from datetime import datetime
from flask_login import UserMixin
import pytz

print("from models")

# Define IST timezone
IST = pytz.timezone("Asia/Kolkata")

# ------------------- User Model -------------------
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(50))
    otp_secret = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))  # ⏰ IST time

    def __repr__(self):
        return f"<User {self.id} - {self.name} - {self.role}>"


# ------------------- Flask-Login Loader -------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ------------------- Video Model -------------------
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    filename = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))  # ⏰ IST time

    def __repr__(self):
        return f"<Video {self.id} - {self.title}>"


# ------------------- Watch History Model -------------------
class WatchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trainee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    watched_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))  # ⏰ IST time

    trainee = db.relationship('User', backref='watch_history', lazy=True)
    video = db.relationship('Video', backref='watched_by', lazy=True)

    def __repr__(self):
        return f"<WatchHistory User={self.trainee_id}, Video={self.video_id}, Watched={self.watched_at}>"


# ------------------- Notes Model -------------------
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Note {self.title}>"




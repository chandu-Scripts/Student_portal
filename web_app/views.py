from flask import render_template, redirect, url_for, request, session, flash
from flask_login import login_user, logout_user, login_required, current_user
from web_app import db, mail, login_manager
from app import app
from web_app.models import User, Video, WatchHistory,Note

from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory

print("from views")

@app.route('/')
def index():
    return redirect(url_for('login'))

# ------------------- Register -------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(email=email, role=role).first()
        if existing_user:
            flash('User already exists with this email and role!', 'danger')
            return redirect(url_for('register'))

        otp_secret = pyotp.random_base32()
        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role,
            otp_secret=otp_secret,
            created_at=datetime.utcnow()
        )

        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# ------------------- Login -------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        user = User.query.filter_by(email=email, role=role).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['email'] = user.email

            otp = pyotp.TOTP(user.otp_secret).now()
            msg = Message('Your OTP Code', recipients=[user.email])
            msg.body = f'Your OTP is: {otp}'
            mail.send(msg)

            flash('OTP sent to your email.', 'info')
            return redirect(url_for('verify_otp'))
        else:
            flash('Invalid credentials.', 'danger')

    return render_template('login.html')


# ------------------- OTP Verification -------------------
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        user_id = session.get('user_id')

        if not user_id:
            flash("Session expired. Please login again.", "danger")
            return redirect(url_for('login'))

        user = User.query.get(user_id)

        if user and user.otp_secret:
            totp = pyotp.TOTP(user.otp_secret)
            if totp.verify(entered_otp, valid_window=1):  # ✅ allow slight drift
                session['verified'] = True
                session['user_id'] = user.id
                session['username'] = user.name
                session['role'] = user.role
                session['logged_in'] = True

                login_user(user)
                flash("OTP verified successfully.", "success")
                return redirect(url_for('home'))

        flash("Invalid OTP. Please try again.", "danger")

    return render_template('verify_otp.html')



# ------------------- Home Page -------------------
@app.route('/home')
def home():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    return render_template('home.html', user=user)


# ------------------- Logout -------------------
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ------------------- Upload Video -------------------
@app.route('/upload', methods=['GET', 'POST'])
def upload_video():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to upload videos.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(user_id)

    if user.role != 'Management':
        flash('Only Management can upload videos.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form['title']
        video = request.files.get('video')

        if not video:
            flash('No video file selected.', 'danger')
            return redirect(request.url)

        filename = secure_filename(video.filename)

        if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in app.config['ALLOWED_EXTENSIONS']:
            flash('Invalid video format. Allowed formats: mp4, mov, avi, mkv', 'danger')
            return redirect(request.url)

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video.save(file_path)

        video_record = Video(
            title=title,
            filename=filename,
            uploaded_at=datetime.utcnow()
        )
        db.session.add(video_record)
        db.session.commit()

        flash('Video uploaded successfully!', 'success')
        return redirect(url_for('upload_video'))

    return render_template('upload_video.html')


# ------------------- View Videos -------------------
@app.route('/view_videos')
def view_videos():
    user_id = session.get('user_id')
    role = session.get('role')

    if not user_id:
        flash("Please login to continue.", "warning")
        return redirect(url_for('login'))

    videos = Video.query.order_by(Video.uploaded_at.desc()).all()
    return render_template('view_videos.html', videos=videos, user_id=user_id, role=role)


# ------------------- Watch Video -------------------
@app.route('/watch_video/<int:video_id>')
def watch_video(video_id):
    if not session.get('logged_in'):
        flash("Please log in to view videos.", "warning")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user_role = session.get('role')

    # First, validate video exists before logging
    video = Video.query.get(video_id)
    if not video:
        flash("Video not found.", "warning")
        return redirect(url_for('view_videos'))

    # ✅ Only Trainee logs history
    if user_role == 'Trainee':
        existing = WatchHistory.query.filter_by(trainee_id=user_id, video_id=video_id).first()
        if not existing:
            history = WatchHistory(trainee_id=user_id, video_id=video_id)
            db.session.add(history)
            db.session.commit()
            print(f"✅ Watch history recorded: Trainee {user_id} watched Video {video_id}")
        else:
            print("🟡 Already watched this video — not logging again.")

    return render_template("watch_video.html", video=video)





# ------------------- Delete Video -------------------
@app.route('/delete_video/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if not user or user.role != 'Management':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    video = Video.query.get(video_id)
    if video:
        db.session.delete(video)
        db.session.commit()

        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
        if os.path.exists(video_path):
            os.remove(video_path)

        flash('Video deleted successfully.', 'success')
    else:
        flash('Video not found.', 'warning')

    return redirect(url_for('view_videos'))


# ------------------- Edit Video -------------------
@app.route('/edit_video/<int:video_id>', methods=['GET', 'POST'])
def edit_video(video_id):
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if not user or user.role != 'Management':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    video = Video.query.get(video_id)
    if not video:
        flash('Video not found.', 'warning')
        return redirect(url_for('view_videos'))

    if request.method == 'POST':
        new_title = request.form['title']
        video.title = new_title
        db.session.commit()
        flash('Video title updated successfully.', 'success')
        return redirect(url_for('view_videos'))

    return render_template('edit_video.html', video=video)


# ------------------- Watch History (Management) -------------------
@app.route('/watch_history')
def watch_history():
    # 🔐 Check if user is logged in and is Management
    if not session.get('logged_in'):
        flash("Please log in to view watch history.", "warning")
        return redirect(url_for('login'))

    if session.get('role') != 'Management':
        flash("Unauthorized access. Only Management can view watch history.", "danger")
        return redirect(url_for('home'))

    # ✅ Query joined WatchHistory + User + Video
    history = (
        db.session.query(WatchHistory, User, Video)
        .join(User, WatchHistory.trainee_id == User.id)
        .join(Video, WatchHistory.video_id == Video.id)
        .order_by(WatchHistory.watched_at.desc())
        .all()
    )

    print(f"DEBUG - History entries: {len(history)}")  # Debug count
    return render_template("watch_history.html", history=history)



# ------------------- Login Manager Loader -------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

from web_app.models import Note  # import Note model

# ---------------- Upload Notes ----------------
@app.route('/upload_notes', methods=['GET', 'POST'])
def upload_notes():
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if not user or user.role != 'Management':
        flash("Unauthorized access. Only Management can upload notes.", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form['title']
        file = request.files.get('note')

        if not file:
            flash("Please choose a file to upload.", "danger")
            return redirect(request.url)

        if not allowed_note_file(file.filename):
            flash("Invalid file type. Only PDFs, DOCs, PPTs, XLS allowed.", "danger")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['NOTES_UPLOAD_FOLDER'], filename)
        file.save(filepath)

        note = Note(title=title, filename=filename, uploaded_at=datetime.utcnow())
        db.session.add(note)
        db.session.commit()

        flash("Note uploaded successfully.", "success")
        return redirect(url_for('upload_notes'))

    return render_template('upload_notes.html')


# ---------------- View Notes ----------------
@app.route('/view_notes')
def view_notes():
    if not session.get('logged_in'):
        flash("Please login to continue.", "warning")
        return redirect(url_for('login'))

    notes = Note.query.order_by(Note.uploaded_at.desc()).all()
    return render_template('view_notes.html', notes=notes)



@app.route('/download_note/<filename>')
def download_note(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


# ------------------- Delete Note -------------------
@app.route('/delete_note/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if not user or user.role != 'Management':
        flash("Unauthorized access. Only Management can delete notes.", "danger")
        return redirect(url_for('view_notes'))

    note = Note.query.get(note_id)
    if note:
        # Delete file from storage
        note_path = os.path.join(app.config['NOTES_UPLOAD_FOLDER'], note.filename)
        if os.path.exists(note_path):
            os.remove(note_path)

        # Delete from database
        db.session.delete(note)
        db.session.commit()
        flash("Note deleted successfully.", "success")
    else:
        flash("Note not found.", "warning")

    return redirect(url_for('view_notes'))


def allowed_note_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_NOTE_EXTENSIONS']


# Step 1: Add a new route for /dashboard in views.py

# @app.route('/dashboard')
# def dashboard():
#     if not session.get('logged_in'):
#         flash("Please log in to access the dashboard.", "warning")
#         return redirect(url_for('login'))
#
#     if session.get('role') != 'Management':
#         flash("Only Management can view the dashboard.", "danger")
#         return redirect(url_for('home'))
#
#     # Get counts
#     total_users = User.query.count()
#     total_trainees = User.query.filter_by(role='Trainee').count()
#     total_management = User.query.filter_by(role='Management').count()
#     total_videos = Video.query.count()
#     total_notes = Note.query.count()
#     recent_history = (
#         db.session.query(WatchHistory, User, Video)
#         .join(User, WatchHistory.trainee_id == User.id)
#         .join(Video, WatchHistory.video_id == Video.id)
#         .order_by(WatchHistory.watched_at.desc())
#         .limit(5)
#         .all()
#     )
#
#     return render_template(
#         'dashboard.html',
#         total_users=total_users,
#         total_trainees=total_trainees,
#         total_management=total_management,
#         total_videos=total_videos,
#         total_notes=total_notes,
#         recent_history=recent_history
#     )

# ------------------- Dashboard Stats (Management Only) -------------------
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in') or session.get('role') != 'Management':
        flash("Only Management can access the dashboard.", "danger")
        return redirect(url_for('home'))

    total_users = User.query.count()
    total_trainees = User.query.filter_by(role='Trainee').count()
    total_management = User.query.filter_by(role='Management').count()
    total_videos = Video.query.count()
    total_notes = Note.query.count()
    total_watches = WatchHistory.query.count()

    return render_template(
        'dashboard.html',
        total_users=total_users,
        total_trainees=total_trainees,
        total_management=total_management,
        total_videos=total_videos,
        total_notes=total_notes,
        total_watches=total_watches
    )

from flask import Flask, render_template, flash, redirect, url_for, session, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_migrate import Migrate   # ✅ importantpip install --upgrade Flask-SQLAlchemy

import os
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ai_for_wildlife.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)



# =====================================
#           Database Creation
# =====================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_banned = db.Column(db.Boolean, default=False, nullable=False)

class AdminData(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Auto-increment automatically in SQLite
    admin_username = db.Column(db.String(50), unique=True, nullable=False)
    admin_email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


class DetectionHistory(db.Model):
    __tablename__ = 'detection_history'

    id = db.Column(db.Integer, primary_key=True)

    # 'image', 'video', 'live', 'mobile'
    source_type = db.Column(db.String(20), nullable=False)

    # For image/video: upload path
    # For live: e.g. 'laptop_camera_0'
    # For mobile: the mobile stream URL
    input_path = db.Column(db.String(500), nullable=True)

    # Final processed media:
    # - image: annotated output image path
    # - video: annotated MP4 path
    # - live/mobile: can be empty or last frame path
    output_path = db.Column(db.String(500), nullable=True)

    # Comma-separated list of screenshot paths (for video/live/mobile)
    screenshot_paths = db.Column(db.Text, nullable=True)

    # Comma-separated labels detected in this session
    detected_labels = db.Column(db.Text, nullable=True)

    # Number of poacher detections (e.g. unique ones)
    poacher_count = db.Column(db.Integer, default=0, nullable=False)

    # Whether an email was sent in this session
    email_sent = db.Column(db.Boolean, default=False, nullable=False)

    # Session timing
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ended_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<DetectionHistory {self.id} {self.source_type} {self.input_path}>"



# ================================================
#           Common helper function
# ================================================



def log_detection(
    source_type: str,
    input_path: str | None,
    output_path: str | None,
    screenshot_paths: list[str],
    detected_labels: list[str],
    poacher_count: int,
    email_sent: bool,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
):
    history = DetectionHistory(
        source_type=source_type,
        input_path=input_path,
        output_path=output_path,
        screenshot_paths=",".join(screenshot_paths) if screenshot_paths else "",
        detected_labels=",".join(sorted(set(detected_labels))) if detected_labels else "",
        poacher_count=poacher_count,
        email_sent=email_sent,
        started_at=started_at or datetime.utcnow(),
        ended_at=ended_at or datetime.utcnow(),
    )
    db.session.add(history)
    db.session.commit()


# ================================================
#           Global Email Configuration
# ================================================

# Sender ( send email from this mail )
EMAIL_SENDER = "vedanthendre10@gmail.com"
EMAIL_PASSWORD = "prnx mwvo qsui xadj"

# receiver ( receive email on this mail )
EMAIL_RECEIVER = "shampanchwagh29@gmail.com"





@app.route('/')
def base():
    return render_template('new_main.html')


# ===============================================
#                  OTP Based Login
# ===============================================

from flask_mail import Mail, Message
import random
import time


# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # your mail server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = EMAIL_SENDER  # replace with your email
app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD  # replace with your email password

mail = Mail(app)

# Store OTP and timestamp
otp_storage = {}

# Function to send OTP
def send_otp(email):
    otp = random.randint(100000, 999999)
    otp_storage[email] = {
        "otp": otp,
        "time": time.time()
    }

    msg = Message(
        subject="Your OTP for Login",
        sender=app.config['MAIL_USERNAME'],
        recipients=[email]
    )
    msg.body = (
        f"AI For Wildlife Monitoring And Poaching Detection\n"
        f"Your OTP is {otp}. Please use this to log in.\n"
        f"OTP is valid for 10 minutes only."
    )
    mail.send(msg)
    print("OTP Storage:", otp_storage)  # Debugging


@app.route('/otp-login', methods=['GET', 'POST'])
def otp_login_home():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash("Email is required", "danger")
            return redirect(url_for('otp_login_home'))

        # Check if email exists in DB
        user = User.query.filter_by(email=email).first()
        if user:
            session['otp_email'] = email
            send_otp(email)
            flash(f"OTP sent successfully to {email}", "success")
            return redirect(url_for('verify_otp'))
        else:
            flash("Email is not registered", "danger")
            return redirect(url_for('otp_login_home'))

    return render_template('OTP/otp_login_home.html')


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp = request.form.get('otp')
        email = session.get('otp_email')
        current_time = time.time()

        if not otp:
            flash("OTP is required", "danger")
            return redirect(url_for('verify_otp'))

        if not email or email not in otp_storage:
            flash("No OTP found. Please request again.", "danger")
            return redirect(url_for('otp_login_home'))

        stored_otp = otp_storage[email]["otp"]
        otp_time = otp_storage[email]["time"]

        # Check expiry
        if current_time - otp_time > 600: #( 10 Minutes == 600 seconds )
            otp_storage.pop(email, None)
            flash("OTP has expired. Please request a new one.", "error")
            return redirect(url_for('otp_login_home'))

        # Check OTP match
        if otp.isdigit() and int(otp) == stored_otp:
            user = User.query.filter_by(email=email).first()
            session['user_id'] = user.id
            session['user_name']=user.username
            session['user_email']=user.email
            session['logged_in']=True

            # Cleanup
            otp_storage.pop(email, None)
            session.pop('otp_email', None)

            return redirect(url_for('user_home'))

        flash("Invalid OTP", "danger")
        return redirect(url_for('verify_otp'))

    return render_template('OTP/verify_otp.html')


@app.route('/resend-otp')
def resend_otp():
    email = session.get('otp_email')
    if not email:
        flash("No email found. Please login again.", "error")
        return redirect(url_for('otp_login_home'))

    send_otp(email)
    flash(f"New OTP has been sent to {email}", "success")
    return redirect(url_for('verify_otp'))







# ==========================================
#           Regular Functions
# ==========================================


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_username = request.form.get('email')
        password = request.form.get('password')

        try:
            # Check by email first
            user = User.query.filter_by(email=email_or_username).first()

            # If not found, check by username
            if not user:
                user = User.query.filter_by(username=email_or_username).first()

            # If still not found → invalid credentials
            if not user:
                flash("Invalid credentials.", "danger")
                return redirect(url_for('login'))

            # Check if banned
            if user.is_banned:
                flash("Your account is banned. You cannot log in.", "danger")
                return redirect(url_for('login'))

            # Validate password
            if not check_password_hash(user.password, password):
                flash("Invalid credentials.", "danger")
                return redirect(url_for('login'))

            # Successful login
            session['user_id'] = user.id
            session['user_name'] = user.username
            session['logged_in'] = True

            flash("Login successful.", "success")
            return redirect(url_for('user_home'))

        except Exception as e:
            flash("Invalid credentials.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')





def login_required(f):
    """
    Decorator to protect routes that require authentication.
    Redirects to login page if user is not logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('logged_in'):
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        banned_user = User.query.filter_by(email=email, is_banned=True).first()
        if banned_user:
            flash("You are banned from registering.", "danger")
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already registered. Please login.', 'warning')
            return redirect(url_for('login'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')



@app.route('/logout/')
def logout():
    session.pop('user_id', None)
    flash('Logout Successfully', 'danger')
    return redirect(url_for('base'))


@app.route('/pre')
@login_required
def pre():
    return render_template('predict_selection.html')


@app.route('/user_home')
@login_required
def user_home():
    # Retrieve user data from session
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    user_email = session.get('user_email')

    # Pass data to template
    return render_template(
        'user_home.html',
        user_id=user_id,
        user_name=user_name.title(),
        user_email=user_email
    )


@app.route('/contact')
@login_required
def contact():
    return render_template('contact.html')


@app.route('/about')
def about():
    return render_template('about.html')





# =====================================================
# Model Loading And Folder Configuration
# =====================================================

from ultralytics import YOLO

model = None

def get_model():
    global model
    if model is None:
        model = YOLO("best.pt")
    return model

# Folder Configuration
UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "static/results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)



# =====================================================
#                    Video Detection
# =====================================================



# ============================================================
#              Send Alert When Poacher detected
# ============================================================

import cv2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage


# =================================================
#                       EMAIL Alert
# =================================================


def send_email_alert_multiple(screenshot_paths):

    msg = MIMEMultipart()
    msg["Subject"] = "🚨 Poacher Alert Detected (Video)"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    msg.attach(MIMEText("Poachers have been detected. Please find the screenshots attached.", "plain"))

    for path in screenshot_paths:
        with open(path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(path))
            msg.attach(img)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        print("📧 Email alert sent successfully (video)!")


# =================================================
#                       SMS Alert
# =================================================

def send_sms_alert():
    # Example using Twilio
    from twilio.rest import Client
    account_sid = "your_sid"
    auth_token = "your_auth_token"
    client = Client(account_sid, auth_token)

    client.messages.create(
        body="🚨 ALERT: Poacher detected in wildlife zone!",
        from_="+1234567890",
        to="+919876543210"
    )
    print("📱 SMS alert sent successfully!")


# =====================================================
#                    Video Detection
# =====================================================

import os
from ultralytics import YOLO
from moviepy.editor import VideoFileClip

# convert .avi file to .mp4 file
def convert_to_mp4(input_path, output_path):
    """Convert AVI to MP4 using moviepy"""
    clip = VideoFileClip(input_path)
    clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    clip.close()


from datetime import datetime

@app.route('/predict_video', methods=['GET', 'POST'])
@login_required
def predict_video():
    if request.method == 'POST':
        started_at = datetime.utcnow()   # 👈 NEW

        video = request.files['video']
        if video.filename == '':
            return "No file selected", 400

        filepath = os.path.join(UPLOAD_FOLDER, video.filename)
        video.save(filepath)

        screenshot_dir = os.path.join(RESULTS_FOLDER, "video_screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        results = get_model().predict(
            source=filepath,
            save=True,
            project=RESULTS_FOLDER,
            name="runs",
            exist_ok=True
        )

        save_dir = results[0].save_dir

        avi_file = None
        for file in os.listdir(save_dir):
            if file.endswith(".avi"):
                avi_file = os.path.join(save_dir, file)
                break
        if avi_file is None:
            return "No AVI output found", 500

        cap = cv2.VideoCapture(filepath)
        frame_count = 0
        screenshots = []              # 👈 collect all screenshot paths
        detected_labels_set = set()   # 👈 collect labels

        last_detection_coords = None
        detection_threshold = 50
        detection_cooldown = 30
        cooldown_counter = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1

            if cooldown_counter > 0:
                cooldown_counter -= 1
                continue

            frame_results = get_model().predict(frame, conf=0.5, verbose=False)
            annotated_frame = frame_results[0].plot()

            for box in frame_results[0].boxes:
                cls_id = int(box.cls[0])
                label = get_model().names[cls_id]
                label_lower = label.lower()
                detected_labels_set.add(label_lower)   # 👈 NEW

                if label_lower == "poacher":
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2

                    if (
                        last_detection_coords is None or
                        abs(center_x - last_detection_coords[0]) > detection_threshold or
                        abs(center_y - last_detection_coords[1]) > detection_threshold
                    ):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = os.path.join(
                            screenshot_dir, f"poacher_frame_{frame_count}_{timestamp}.jpg"
                        )
                        cv2.imwrite(screenshot_path, annotated_frame)
                        screenshots.append(screenshot_path)   # 👈 NEW
                        print(f"📸 Unique poacher detected at frame {frame_count}")

                        last_detection_coords = (center_x, center_y)
                        cooldown_counter = detection_cooldown
                    break

        cap.release()

        email_sent = False
        poacher_count = len(screenshots)
        if screenshots:
            send_email_alert_multiple(screenshots)
            email_sent = True
            print(f"🚨 Alert sent! {len(screenshots)} unique poacher detections found.")

        mp4_filename = os.path.splitext(os.path.basename(avi_file))[0] + ".mp4"
        mp4_path = os.path.join(save_dir, mp4_filename)
        convert_to_mp4(avi_file, mp4_path)
        os.remove(avi_file)

        # 👈 NEW: log to DB
        ended_at = datetime.utcnow()
        log_detection(
            source_type="video",
            input_path=filepath,
            output_path=mp4_path,
            screenshot_paths=screenshots,
            detected_labels=list(detected_labels_set),
            poacher_count=poacher_count,
            email_sent=email_sent,
            started_at=started_at,
            ended_at=ended_at
        )

        return redirect(url_for('show_result', filename=mp4_filename))

    return render_template('predict_video.html')




@app.route('/results/<filename>')
@login_required
def show_result(filename):
    return render_template("show_result.html", filename=filename)

@app.route('/results/videos/<filename>')
def result_video(filename):
    return send_from_directory(os.path.join(RESULTS_FOLDER, "runs"), filename)





# ===========================================================
#                         Image Detection
# ===========================================================


# ===========================================================
#             Send Alert For Image Detection
# ===========================================================
def send_email_alert_image(image_path):

    msg = MIMEMultipart()
    msg["Subject"] = "🚨 Poacher Alert Detected (Image)"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    msg.attach(MIMEText("A poacher has been detected. Please find the attached image.", "plain"))

    with open(image_path, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
        msg.attach(img)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        print("📧 Email alert sent successfully (image)!")


from datetime import datetime

@app.route('/predict_image', methods=['GET', 'POST'])
@login_required
def predict_image():
    if request.method == 'POST':
        started_at = datetime.utcnow()           # 👈 NEW
        image = request.files['image']
        if image.filename == '':
            return "No file selected", 400

        filepath = os.path.join(UPLOAD_FOLDER, image.filename)
        image.save(filepath)

        results = get_model().predict(
            source=filepath,
            save=True,
            project=RESULTS_FOLDER,
            name="image_runs",
            exist_ok=True
        )

        save_dir = results[0].save_dir

        detected_images = [
            os.path.join(save_dir, f)
            for f in os.listdir(save_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ]
        if not detected_images:
            return "No output image found", 500

        detected_image = max(detected_images, key=os.path.getmtime)

        # Labels
        detected_labels = []
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            detected_labels.append(get_model().names[cls_id].lower())

        is_poacher = "poacher" in detected_labels
        email_sent = False
        if is_poacher:
            send_email_alert_image(detected_image)
            email_sent = True
            print("🚨 Poacher detected! Email alert sent.")
        else:
            print("✅ No poacher detected in image.")

        # 👈 NEW: log to DB
        ended_at = datetime.utcnow()
        poacher_count = 1 if is_poacher else 0
        log_detection(
            source_type="image",
            input_path=filepath,
            output_path=detected_image,
            screenshot_paths=[detected_image] if is_poacher else [],
            detected_labels=detected_labels,
            poacher_count=poacher_count,
            email_sent=email_sent,
            started_at=started_at,
            ended_at=ended_at
        )

        return redirect(url_for('show_image_result', filename=os.path.basename(detected_image)))

    return render_template('predict_image.html')



@app.route('/show_image_result/<filename>')
@login_required
def show_image_result(filename):
    return render_template('show_image_result.html', filename=filename)







# ===========================================================
#                         Camera Detection
# ===========================================================

from datetime import datetime
# from playsound import playsound  # simple library to play audio
import cv2, os, threading




# Folder where audio is stored
AUDIO_FOLDER = "static/audio"
WARNING_SOUND = os.path.join(AUDIO_FOLDER, "siren.mp3")  # make sure this file exists

#
# @app.route('/predict_camera')
# @login_required
# def predict_camera():
#     cap = cv2.VideoCapture(0)  # Open laptop camera
#     if not cap.isOpened():
#         flash("Error: Could not open camera.", "danger")
#         return redirect(url_for('pre'))
#
#     detected_once = False  # To prevent multiple email alerts
#
#     def play_warning_sound():
#         """Play siren sound in background."""
#         if os.path.exists(WARNING_SOUND):
#             playsound(WARNING_SOUND, block=False)
#
#     def send_alert_async(image_path):
#         """Send alert email in background."""
#         threading.Thread(target=send_email_alert_image, args=(image_path,), daemon=True).start()
#
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break
#
#         # Resize frame to improve performance
#         frame_resized = cv2.resize(frame, (640, 480))
#
#         # Run YOLOv8 detection
#         results = model.predict(source=frame_resized, imgsz=640, conf=0.5, verbose=False)
#         annotated_frame = results[0].plot()  # Annotated frame with boxes
#
#         # Extract detected labels
#         detected_labels = [model.names[int(box.cls[0])].lower() for box in results[0].boxes]
#
#         if "poacher" in detected_labels:
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             screenshot_path = os.path.join("static/results", "camera_screenshots")
#             os.makedirs(screenshot_path, exist_ok=True)
#             screenshot_file = os.path.join(screenshot_path, f"poacher_{timestamp}.jpg")
#
#             # ✅ Save annotated frame instead of raw frame
#             cv2.imwrite(screenshot_file, annotated_frame)
#
#             # Play warning sound (non-blocking)
#             threading.Thread(target=play_warning_sound, daemon=True).start()
#
#             # Send email alert only once (with annotated image)
#             if not detected_once:
#                 send_alert_async(screenshot_file)
#                 print(f"🚨 Poacher detected! Annotated screenshot saved: {screenshot_file}")
#                 detected_once = True
#
#         # Display annotated video
#         cv2.imshow("Live Poacher Detection (Press 'q' to Quit)", annotated_frame)
#
#         # Quit if 'q' pressed
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
#
#     cap.release()
#     cv2.destroyAllWindows()
#
#     flash("Camera Detection Stopped Successfully.", "success")
#     return redirect(url_for('pre'))


@app.route('/predict_camera')
@login_required
def predict_camera():
    import cv2
    import os
    import threading
    #import tkinter as tk
    from tkinter import messagebox
    from PIL import Image, ImageTk
    from datetime import datetime
    from playsound import playsound

    global model, WARNING_SOUND
    detection_active = True
    started_at = datetime.utcnow()


    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        flash("Error: Could not open camera.", "danger")
        return redirect(url_for('pre'))

    screenshot_files = []
    detected_labels_set = set()

    # NEW: track per-session poacher events
    in_poacher_event = False      # True while poacher continuously visible
    poacher_event_count = 0       # How many times we started a new event

    def play_warning_sound():
        if os.path.exists(WARNING_SOUND):
            playsound(WARNING_SOUND, block=False)

    def send_alert_async(image_path):
        threading.Thread(
            target=send_email_alert_image,
            args=(image_path,),
            daemon=True
        ).start()

    def stop_detection():
        nonlocal detection_active
        detection_active = False

    # ------------------------
    # MAIN DETECTION LOOP
    # ------------------------
    def start_detection(window, video_label):
        nonlocal detection_active, screenshot_files, detected_labels_set
        nonlocal in_poacher_event, poacher_event_count

        while detection_active:
            ret, frame = cap.read()
            if not ret:
                break

            frame_resized = cv2.resize(frame, (640, 480))

            # Run YOLO
            results = model.predict(source=frame_resized, imgsz=640, conf=0.5, verbose=False)
            annotated_frame = results[0].plot()

            # Collect all labels
            detected_labels = [model.names[int(box.cls[0])].lower()
                               for box in results[0].boxes]
            for lbl in detected_labels:
                detected_labels_set.add(lbl)

            poacher_now = ("poacher" in detected_labels)

            # ------------------------
            # NEW POACHER EVENT LOGIC
            # ------------------------
            if poacher_now and not in_poacher_event:
                # Transition: no poacher -> poacher detected
                in_poacher_event = True
                poacher_event_count += 1

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_dir = os.path.join("static/results", "camera_screenshots")
                os.makedirs(screenshot_dir, exist_ok=True)

                screenshot_file = os.path.join(screenshot_dir, f"poacher_{timestamp}.jpg")
                cv2.imwrite(screenshot_file, annotated_frame)
                screenshot_files.append(screenshot_file)

                # Siren once per event
                threading.Thread(target=play_warning_sound, daemon=True).start()

                # Email once per event
                send_alert_async(screenshot_file)
                print(f"🚨 Poacher EVENT #{poacher_event_count} – Email sent, saved: {screenshot_file}")

            elif not poacher_now and in_poacher_event:
                # Transition: poacher was present, now gone -> end event
                in_poacher_event = False
                print("ℹ️ Poacher left the frame – event ended.")

            # ------------------------
            # Update Tkinter image
            # ------------------------
            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(frame_rgb))

            video_label.config(image=img)
            video_label.image = img

            window.update_idletasks()
            window.update()

        cap.release()
        cv2.destroyAllWindows()
        window.destroy()
        print("🛑 Detection stopped.")

    # ------------------------
    # TKINTER UI
    # ------------------------
    window = tk.Tk()
    window.title("Camera Detection")
    window.geometry("700x550")

    video_label = tk.Label(window)
    video_label.pack(pady=10)

    stop_button = tk.Button(window, text="Stop Detection", command=stop_detection)
    stop_button.pack(pady=5)

    # Run detection loop directly (NO THREAD)
    start_detection(window, video_label)

    # After window closes: save log
    ended_at = datetime.utcnow()

    email_sent = (poacher_event_count > 0)

    log_detection(
        source_type="live",
        input_path="laptop_camera_0",
        output_path=None,
        screenshot_paths=screenshot_files,
        detected_labels=list(detected_labels_set),
        poacher_count=poacher_event_count,   # number of events, not frames
        email_sent=email_sent,
        started_at=started_at,
        ended_at=ended_at
    )

    flash("Camera Detection Stopped Successfully.", "danger")
    return redirect(url_for('pre'))



#
# ================================================================
#                           Mobile Camera
# =================================================================


from flask import Flask, redirect, url_for, flash
#from flask_login import login_required
import cv2
import threading
import os
#import tkinter as tk
#from PIL import Image, ImageTk
#from datetime import datetime
#from playsound import playsound
#from flask_login import LoginManager




# Global variables
MOBILE_CAMERA_URL = "http://192.168.1.36:8080/video"  # Your mobile IP webcam URL


@app.route('/predict_mobile_camera')
def predict_mobile_camera():
    detection_active = True
    detected_once = False

    cap = cv2.VideoCapture(MOBILE_CAMERA_URL)
    if not cap.isOpened():
        flash("Error: Could not open mobile camera stream.", "danger")
        return redirect(url_for('pre'))

    # Tkinter Window
    window = tk.Tk()
    window.title("Live Poacher Detection - Mobile Camera")
    window.geometry("720x580+20+10")
    window.resizable(False, False)
    window.configure(bg="black")

    tk.Label(window, text="Mobile Wildlife & Poacher Detection",
             font=("Arial", 18, "bold"), bg="black", fg="white").pack(pady=10)

    video_label = tk.Label(window, bg="black", width=640, height=480)
    video_label.pack(padx=10, pady=10)

    # Stop button
    def stop_detection():
        nonlocal detection_active
        detection_active = False

    tk.Button(window, text="Close Detection", font=("Arial", 14, "bold"),
              bg="red", fg="white", width=20, command=stop_detection).pack(pady=15)

    # Play siren
    def play_warning_sound():
        if os.path.exists(WARNING_SOUND):
            playsound(WARNING_SOUND, block=False)

    # Send email async
    def send_alert_async(image_path):
        threading.Thread(target=send_email_alert_image, args=(image_path,), daemon=True).start()

    # Detection loop
    def start_detection():
        nonlocal detected_once, detection_active
        while detection_active:
            ret, frame = cap.read()
            if not ret:
                continue

            frame_resized = cv2.resize(frame, (640, 480))
            results = model.predict(source=frame_resized, imgsz=640, conf=0.5, verbose=False)
            annotated_frame = results[0].plot()
            detected_labels = [model.names[int(box.cls[0])].lower() for box in results[0].boxes]

            if "poacher" in detected_labels:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join("static/results/mobile_camera_screenshots")
                os.makedirs(screenshot_path, exist_ok=True)
                screenshot_file = os.path.join(screenshot_path, f"poacher_{timestamp}.jpg")
                cv2.imwrite(screenshot_file, annotated_frame)

                threading.Thread(target=play_warning_sound, daemon=True).start()
                if not detected_once:
                    send_alert_async(screenshot_file)
                    print(f"🚨 Poacher detected! Screenshot saved: {screenshot_file}")
                    detected_once = True

            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.imgtk = imgtk
            video_label.config(image=imgtk)
            video_label.update_idletasks()

            window.update()
            window.after(10)

        cap.release()
        cv2.destroyAllWindows()
        window.destroy()
        print("🛑 Mobile Camera Detection stopped.")

    threading.Thread(target=start_detection, daemon=True).start()
    window.mainloop()

    flash("Mobile Camera Detection Stopped Successfully.", "success")
    return redirect(url_for('pre'))






# ==========================================
#                 Admin Login
# ==========================================

# Admin Login
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_username = request.form.get('admin_username')
        password = request.form.get('password')

        # Check credentials
        admin_obj = AdminData.query.filter_by(admin_username=admin_username, password=password).first()
        if not admin_obj:
            admin_obj = AdminData.query.filter_by(admin_email=admin_username, password=password).first()

        if admin_obj:
            session['admin_username'] = admin_obj.admin_username
            flash("Successfully logged in", "success")
            return redirect(url_for('admin_home'))
        else:
            flash("Invalid Username or Password...!", "danger")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


# Admin Registration
@app.route('/admin_registration/', methods=['GET', 'POST'])
def admin_registration():
    if request.method == 'POST':
        admin_username = request.form.get('admin_username')
        email = request.form.get('email')
        pass1 = request.form.get('password')
        pass2 = request.form.get('confirm_password')

        if pass1 != pass2:
            flash('Both passwords are not matched', 'danger')
            return redirect(url_for('admin_registration'))

        if AdminData.query.filter_by(admin_username=admin_username).first():
            flash('Admin username already exists', 'danger')
            return redirect(url_for('admin_registration'))

        # Save admin
        new_admin = AdminData(admin_username=admin_username, admin_email=email, password=pass1)
        db.session.add(new_admin)
        db.session.commit()
        flash(f'The admin {admin_username} is saved successfully..!', 'success')
        return redirect(url_for('admin_login'))

    return render_template('admin_registration.html')


# Admin Logout
@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_username', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('base'))

@app.route('/view_file/<path:filename>')
def view_file(filename):
    # serves from static/results/
    return send_from_directory("static/results", filename)

# Admin Home
@app.route('/admin-home')
def admin_home():
    if 'admin_username' not in session:
        flash("Please log in first.", "error")
        return redirect(url_for('admin_login'))

    detections = DetectionHistory.query.order_by(DetectionHistory.started_at.desc()).all()
    return render_template('admin_dir/admin_home.html', detections=detections)


@app.route('/ban-user/<int:user_id>/')
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = True
    db.session.commit()
    flash("User has been banned.", "success")
    return redirect(url_for('view_users'))

@app.route('/unban-user/<int:user_id>/')
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    db.session.commit()
    flash("User has been unbanned.", "success")
    return redirect(url_for('view_users'))


@app.route('/delete-user/<int:user_id>/')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User has been deleted.", "warning")
    return redirect(url_for('view_users'))


@app.route('/view_user/')
def view_users():
    users = User.query.all()
    return render_template('admin_dir/view_user.html', users=users)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

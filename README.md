# 🦁 AI for Wildlife Monitoring and Poaching Prevention

## 📌 Overview

AI for Wildlife Monitoring and Poaching Prevention is an intelligent web-based surveillance system that uses **YOLOv8** object detection and **Artificial Intelligence** to monitor wildlife, detect poachers, and send real-time alerts. The system helps forest authorities respond quickly to illegal activities, contributing to wildlife conservation.

The application supports image, video, live camera, and mobile camera inputs, making it suitable for real-time wildlife monitoring in forests and protected areas.

---

## 🚀 Features

* 🔍 AI-based wildlife and poacher detection using YOLOv8
* 📷 Image Detection
* 🎥 Video Detection
* 📹 Live Camera Detection
* 📱 Mobile Camera Streaming Detection
* 📧 Automatic Email Alert with Detection Screenshots
* 📱 SMS Alert Support (Twilio Integration)
* 👤 User Registration and Login
* 🔐 OTP-Based Login using Email
* 👨‍💼 Admin Dashboard
* 👥 User Management
* 🚫 User Ban/Unban Facility
* 📜 Detection History Storage
* 💾 SQLite Database Integration
* 🌐 Responsive Web Interface using HTML, CSS, and Flask

---

## 🛠️ Technologies Used

### Frontend

* HTML5
* CSS3
* JavaScript

### Backend

* Python
* Flask

### Database

* SQLite
* SQLAlchemy

### Artificial Intelligence

* YOLOv8
* OpenCV
* Ultralytics

### Additional Libraries

* Flask-Mail
* Flask-Migrate
* Werkzeug
* Twilio
* MoviePy

---

## 📂 Project Structure

```text
AI-for-Wildlife-Monitoring-and-Poaching-Prevention/
│
├── app.py
├── mob.py
├── require.txt
├── best.pt
│
├── static/
│   ├── css/
│   ├── images/
│   ├── audio/
│   └── results/
│
├── templates/
│   ├── OTP/
│   ├── admin_dir/
│   └── *.html
│
├── uploads/
├── migrations/
├── instance/
└── README.md
```

---

## ⚙️ Installation

### Clone the Repository

```bash
git clone https://github.com/shambhavip-29/AI-for-Wildlife-Monitoring-and-Poaching-Prevention.git
```

Move into the project folder.

```bash
cd AI-for-Wildlife-Monitoring-and-Poaching-Prevention
```

Install the required packages.

```bash
pip install -r require.txt
```

Run the Flask application.

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

---

## 📸 Modules

### Home Page

Provides information about wildlife monitoring and allows users to navigate through the application.

### User Authentication

* User Registration
* Password Login
* OTP Login using Email

### Admin Module

* Admin Login
* View Users
* Ban/Unban Users
* View Feedback and Ratings

### Image Detection

Users can upload wildlife images for AI-based object detection.

### Video Detection

Upload a recorded video to detect wildlife and poachers.

### Live Camera Detection

Uses the system webcam for real-time object detection.

### Mobile Camera Detection

Supports mobile camera streaming for live wildlife monitoring.

### Alert System

Whenever a poacher is detected:

* Email notification is sent automatically.
* Detection screenshots are attached.
* SMS notification can also be sent using Twilio.

### Detection History

Stores:

* Detection Type
* Input Source
* Output Files
* Screenshots
* Detected Objects
* Detection Time
* Alert Status

---

## 🎯 Objectives

* Protect endangered wildlife species.
* Detect poachers in real time.
* Reduce illegal hunting.
* Assist forest departments using Artificial Intelligence.
* Improve wildlife conservation efforts.

---

## 📊 Future Enhancements

* Drone-based surveillance
* GPS tracking of poachers
* Cloud database integration
* Android application
* Multi-language support
* AI analytics dashboard
* IoT sensor integration
* Automatic forest authority notifications

---

## 👩‍💻 Developed By

**Shambhavi Panchwagh**

Bachelor of Engineering (Computer Science & Engineering)

Savitribai Phule Pune University (SPPU)

---

## 🙏 Acknowledgements

Special thanks to:

* Ultralytics YOLOv8
* Flask Community
* OpenCV
* Python Community
* Wildlife Conservation Organizations

---

## 📄 License

This project is developed for educational and research purposes as a Final Year Engineering Project.

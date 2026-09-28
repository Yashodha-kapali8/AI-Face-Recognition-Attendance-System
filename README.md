# 🎓 AI Face Recognition Attendance System

An AI-powered student attendance management system built with **Django, OpenCV, FaceNet/PyTorch, and SQLite**. The system uses face recognition to identify students and provides **period-wise attendance tracking with check-in and check-out functionality**.

## 📌 Project Overview

The AI Face Recognition Attendance System is designed to automate the traditional attendance process.

Students can register their details and face data, while an administrator can review and approve registrations. Once approved, students can be recognized through the camera and their attendance can be recorded automatically.

The system also supports **period-wise attendance**, allowing students to check in and check out separately for different class periods.

## ✨ Features

- 👤 Student registration
- 🔐 Admin authentication
- ✅ Admin approval for student registrations
- 📸 Face capture and face recognition
- 🤖 AI-based face detection and recognition
- 🕐 Period-wise attendance
- 🟢 Check-in time recording
- 🔴 Check-out time recording
- ⏱️ Attendance duration calculation
- 📊 Student attendance records
- 🗓️ Date-wise attendance tracking
- 🗃️ Django database management

- 🛡️ Prevents duplicate attendance for the same student, date, and period

## 🔄 System Workflow

```text
                    ┌──────────────────┐
                    │  Student Signup  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Face Capture   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Admin Approval   │
                    └────────┬─────────┘
                             │
                         Approved
                             │
                             ▼
                    ┌──────────────────┐
                    │ Face Recognition │
                    └────────┬─────────┘
                             │
                             ▼
                  ┌───────────────────────┐
                  │ Select Class Period  │
                  └───────────┬───────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │    Check In      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    Check Out     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Attendance Record│
                    └──────────────────┘
```
### 🛠️ Technologies Used
* Python
* Django
* OpenCV
* PyTorch
* FaceNet-PyTorch
* MTCNN
* SQLite
* HTML / CSS
* Pygame
### 🚀 How to Run
* Install dependencies
* pip install -r requirements.txt
* Apply migrations
* python manage.py migrate
* Start the server
* python manage.py runserver

### Open:

http://127.0.0.1:8000/
### 🎯 Key Functionality

The system maintains attendance using:

Student + Date + Period

This prevents duplicate attendance for the same student during the same period on the same day.

#### 👨‍💻 Author

**Yashodha Kapali**

GitHub: https://github.com/Yashodha-kapali8

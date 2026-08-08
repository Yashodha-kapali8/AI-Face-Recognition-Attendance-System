import os
import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .models import Student, Attendance
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
from django.utils import timezone
import pygame  # Import pygame for playing sounds
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
import threading
import time
import base64
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import Student
import threading
import time
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Student, Attendance
from twilio.rest import Client
import pygame
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import base64
from django.utils.timezone import now as timezone_now




def home(request):
    return render(request, 'home.html')

def mark_attendance(request):
    return render(request, 'Mark_attendance.html')


# Initialize MTCNN and InceptionResnetV1
mtcnn = MTCNN(keep_all=True)
resnet = InceptionResnetV1(pretrained='vggface2').eval()

# Function to detect and encode faces
def detect_and_encode(image):
    with torch.no_grad():
        boxes, _ = mtcnn.detect(image)
        if boxes is not None:
            faces = []
            for box in boxes:
                face = image[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                if face.size == 0:
                    continue
                face = cv2.resize(face, (160, 160))
                face = np.transpose(face, (2, 0, 1)).astype(np.float32) / 255.0
                face_tensor = torch.tensor(face).unsqueeze(0)
                encoding = resnet(face_tensor).detach().numpy().flatten()
                faces.append(encoding)
            return faces
    return []

# Function to encode uploaded images
def encode_uploaded_images():
    known_face_encodings = []
    known_face_names = []

    # Fetch only authorized images
    uploaded_images = Student.objects.filter(authorized=True)

    for student in uploaded_images:
        image_path = os.path.join(settings.MEDIA_ROOT, str(student.image))
        known_image = cv2.imread(image_path)
        known_image_rgb = cv2.cvtColor(known_image, cv2.COLOR_BGR2RGB)
        encodings = detect_and_encode(known_image_rgb)
        if encodings:
            known_face_encodings.extend(encodings)
            known_face_names.append(student.name)

    return known_face_encodings, known_face_names

# Function to recognize faces
def recognize_faces(known_encodings, known_names, test_encodings, threshold=0.6):
    recognized_names = []
    for test_encoding in test_encodings:
        distances = np.linalg.norm(known_encodings - test_encoding, axis=1)
        min_distance_idx = np.argmin(distances)
        if distances[min_distance_idx] < threshold:
            recognized_names.append(known_names[min_distance_idx])
        else:
            recognized_names.append('Not Recognized')
    return recognized_names

# View for capturing student information and image
def capture_student(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        student_class = request.POST.get('student_class')
        image_data = request.POST.get('image_data')

        # Decode the base64 image data
        if image_data:
            header, encoded = image_data.split(',', 1)
            image_file = ContentFile(base64.b64decode(encoded), name=f"{name}.jpg")

            student = Student(
                name=name,
                email=email,
                phone_number=phone_number,
                student_class=student_class,
                image=image_file,
                authorized=False  # Default to False during registration
            )
            student.save()

            return redirect('selfie_success')  # Redirect to a success page

    return render(request, 'capture_student.html')


# Success view after capturing student information and image
def selfie_success(request):
    return render(request, 'selfie_success.html')


@csrf_exempt
def capture_and_recognize(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data.get('image')
            selected_period = data.get('period')  # Get the selected period from the request

            if not selected_period:
                return JsonResponse({'message': 'No period selected.'}, status=400)
            if not image_data:
                return JsonResponse({'message': 'No image data received.'}, status=400)

            # Decode the image
            image_data = image_data.split(',')[1]  # Remove the prefix
            image_bytes = base64.b64decode(image_data)
            np_img = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Perform face detection and encoding
            test_face_encodings = detect_and_encode(frame_rgb)
            if not test_face_encodings:
                return JsonResponse({'message': 'No face detected.'}, status=200)

            known_face_encodings, known_face_names = encode_uploaded_images()
            if not known_face_encodings:
                return JsonResponse({'message': 'No known faces available.'}, status=200)

            recognized_names = recognize_faces(
                np.array(known_face_encodings), known_face_names, test_face_encodings, threshold=0.6
            )

            attendance_response = []
            for name in recognized_names:
                if name == 'Not Recognized':
                    attendance_response.append({
                        'name': 'Unknown',
                        'period': selected_period,
                        'status': 'Face not recognized',
                        'check_in_time': None,
                        'check_out_time': None
                    })
                else:
                    student = Student.objects.filter(name=name).first()
                    if student:
                        attendance, created = Attendance.objects.get_or_create(
                            student=student,
                            date=timezone_now().date(),
                            period=selected_period
                        )
                        if created:
                            attendance.mark_checked_in()
                            attendance_response.append({
                                'name': name,
                                'period': selected_period,
                                'status': 'Checked-in',
                                'check_in_time': attendance.check_in_time.isoformat(),
                                'check_out_time': None
                            })
                        else:
                            if attendance.check_in_time and not attendance.check_out_time:
                                if timezone_now() >= attendance.check_in_time + timedelta(seconds=60):
                                    attendance.mark_checked_out()
                                    attendance_response.append({
                                        'name': name,
                                        'period': selected_period,
                                        'status': 'Checked-out',
                                        'check_in_time': attendance.check_in_time.isoformat(),
                                        'check_out_time': attendance.check_out_time.isoformat()
                                    })
                                else:
                                    attendance_response.append({
                                        'name': name,
                                        'period': selected_period,
                                        'status': 'Already checked-in',
                                        'check_in_time': attendance.check_in_time.isoformat(),
                                        'check_out_time': None
                                    })
                            elif attendance.check_out_time:
                                attendance_response.append({
                                    'name': name,
                                    'period': selected_period,
                                    'status': 'Already checked-out',
                                    'check_in_time': attendance.check_in_time.isoformat(),
                                    'check_out_time': attendance.check_out_time.isoformat()
                                })

            return JsonResponse({'attendance': attendance_response}, status=200)

        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Invalid request method.'}, status=405)


def student_attendance_list(request):
    # Get the search query and date filter from the request
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('attendance_date', '')

    # Get all students
    students = Student.objects.all()

    # Filter students based on the search query
    if search_query:
        students = students.filter(name__icontains=search_query)

    # Prepare the attendance data
    student_attendance_data = []

    for student in students:
        # Get the attendance records for each student, filtering by attendance date if provided
        attendance_records = Attendance.objects.filter(student=student)

        if date_filter:
            # Assuming date_filter is in the format YYYY-MM-DD
            attendance_records = attendance_records.filter(date=date_filter)

        attendance_records = attendance_records.order_by('date', 'period')
        
        student_attendance_data.append({
            'student': student,
            'attendance_records': attendance_records
        })

    context = {
        'student_attendance_data': student_attendance_data,
        'search_query': search_query,  # Pass the search query to the template
        'date_filter': date_filter       # Pass the date filter to the template
    }
    return render(request, 'student_attendance_list.html', context)





# Custom user pass test for admin access
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def student_list(request):
    students = Student.objects.all()
    return render(request, 'student_list.html', {'students': students})

@login_required
@user_passes_test(is_admin)
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'student_detail.html', {'student': student})

@login_required
@user_passes_test(is_admin)
def student_authorize(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        authorized = request.POST.get('authorized', False)
        student.authorized = bool(authorized)
        student.save()
        return redirect('student-detail', pk=pk)
    
    return render(request, 'student_authorize.html', {'student': student})

# This views is for Deleting student
@login_required
@user_passes_test(is_admin)
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student deleted successfully.')
        return redirect('student-list')  # Redirect to the student list after deletion
    
    return render(request, 'student_delete_confirm.html', {'student': student})


# View function for user login
def user_login(request):
    # Check if the request method is POST, indicating a form submission
    if request.method == 'POST':
        # Retrieve username and password from the submitted form data
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user using the provided credentials
        user = authenticate(request, username=username, password=password)

        # Check if the user was successfully authenticated
        if user is not None:
            # Log the user in by creating a session
            login(request, user)
            # Redirect the user to the student list page after successful login
            return redirect('home')  # Replace 'student-list' with your desired redirect URL after login
        else:
            # If authentication fails, display an error message
            messages.error(request, 'Invalid username or password.')

    # Render the login template for GET requests or if authentication fails
    return render(request, 'login.html')


# This is for user logout
def user_logout(request):
    logout(request)
    return redirect('login')  # Replace 'login' with your desired redirect URL after logout








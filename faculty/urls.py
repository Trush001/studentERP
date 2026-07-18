from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('register/', views.faculty_register, name='faculty_register'),
    path('enrollments/', views.enrollment_requests, name='enrollment_requests'),
    path('batches/', views.batch_management, name='batch_management'),
    path('batches/<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('batches/<int:batch_id>/attendance/', views.mark_attendance, name='mark_attendance'),
    path('assignments/', views.assignment_management, name='assignment_management'),
    path('submissions/<int:submission_id>/review/', views.review_submission, name='review_submission'),
    path('programs/create/', views.create_program, name='create_program'),
]

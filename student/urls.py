from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.student_register, name='student_register'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('programs/', views.program_list, name='student_programs'),
    path('enroll/<int:program_id>/', views.enroll_program, name='enroll_program'),
    path('assignments/', views.assignments_list, name='student_assignments'),
    path('assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
]

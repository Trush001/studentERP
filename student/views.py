from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import User, StudentProfile, Program, Enrollment, Batch, Attendance, Assignment, AssignmentSubmission
from django.contrib import messages
from django.contrib.auth import login

import random
from django.core.mail import send_mail
from django.conf import settings
from core.models import OTPVerification

def student_register(request):
    if request.user.is_authenticated:
        if request.user.is_student:
            return redirect('student_dashboard')
        elif request.user.is_faculty:
            return redirect('faculty_dashboard')
        elif request.user.is_administrator or request.user.is_superuser:
            return redirect('/admin/')
            
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        mobile = request.POST.get('mobile')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('student_register')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email address already exists')
            return redirect('student_register')
        
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            fullname=fullname,
            mobile=mobile,
            is_student=True,
            is_active=False  # Set inactive until OTP is verified
        )
        
        StudentProfile.objects.create(user=user)
        
        # Generate OTP
        otp_code = str(random.randint(100000, 999999))
        OTPVerification.objects.create(user=user, otp_code=otp_code)
        
        # Send Email
        subject = 'Verify your Student ERP Account'
        message = f'Hello {fullname},\n\nYour OTP for registration is: {otp_code}\n\nThank you.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        
        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        except Exception as e:
            messages.error(request, 'Failed to send OTP email. Please try again later.')
            user.delete() # Revert user creation
            return redirect('student_register')
            
        request.session['verification_user_id'] = user.id
        messages.success(request, 'Registration successful. Please verify your email with the OTP sent to you.')
        return redirect('verify_otp')

    return render(request, 'student/register.html')

@login_required
def student_dashboard(request):
    if not request.user.is_student:
        return redirect('login')
    
    profile, created = StudentProfile.objects.get_or_create(user=request.user)
    
    enrollments = Enrollment.objects.filter(student=request.user)
    batches = Batch.objects.filter(students=request.user)
    
    # Calculate attendance %
    total_classes = Attendance.objects.filter(batch__in=batches, student=request.user).count()
    attended_classes = Attendance.objects.filter(batch__in=batches, student=request.user, is_present=True).count()
    attendance_percentage = (attended_classes / total_classes * 100) if total_classes > 0 else 0
    
    context = {
        'student': request.user,
        'profile': profile,
        'enrollments': enrollments,
        'batches': batches,
        'attendance_percentage': round(attendance_percentage, 2)
    }
    return render(request, 'student/dashboard.html', context)

@login_required
def program_list(request):
    if not request.user.is_student:
        return redirect('login')
        
    programs = Program.objects.all()
    enrollments = Enrollment.objects.filter(student=request.user).values_list('program_id', flat=True)
    
    context = {
        'programs': programs,
        'enrolled_program_ids': list(enrollments)
    }
    return render(request, 'student/program_list.html', context)

@login_required
def enroll_program(request, program_id):
    if not request.user.is_student:
        return redirect('login')
        
    if request.method == 'POST':
        program = Program.objects.get(id=program_id)
        Enrollment.objects.get_or_create(
            student=request.user,
            program=program,
            defaults={'status': 'PENDING'}
        )
        messages.success(request, f'Successfully applied for enrollment in {program.name}')
        
    return redirect('student_programs')

@login_required
def assignments_list(request):
    if not request.user.is_student:
        return redirect('login')
        
    batches = Batch.objects.filter(students=request.user)
    assignments = Assignment.objects.filter(batch__in=batches).order_by('-due_date')
    submissions = dict(AssignmentSubmission.objects.filter(student=request.user).values_list('assignment_id', 'status'))
    
    assignments_data = []
    for assignment in assignments:
        assignments_data.append({
            'assignment': assignment,
            'status': submissions.get(assignment.id)
        })
    
    context = {
        'assignments_data': assignments_data
    }
    return render(request, 'student/assignments_list.html', context)

@login_required
def submit_assignment(request, assignment_id):
    if not request.user.is_student:
        return redirect('login')
        
    assignment = Assignment.objects.get(id=assignment_id)
    
    if request.method == 'POST':
        file = request.FILES.get('submitted_file')
        if file:
            submission, created = AssignmentSubmission.objects.update_or_create(
                assignment=assignment,
                student=request.user,
                defaults={
                    'submitted_file': file,
                    'status': 'SUBMITTED'
                }
            )
            messages.success(request, 'Assignment submitted successfully!')
        else:
            messages.error(request, 'Please upload a file.')
            
    return redirect('student_assignments')

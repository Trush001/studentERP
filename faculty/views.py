from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import User, FacultyProfile, Program, Enrollment, Batch, Attendance, Assignment, AssignmentSubmission
from django.contrib import messages
from django.contrib.auth import login

import random
from django.core.mail import send_mail
from django.conf import settings
from core.models import OTPVerification
import json

def faculty_register(request):
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
        subject_param = request.POST.get('subject')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('faculty_register')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email address already exists')
            return redirect('faculty_register')
        
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            fullname=fullname,
            mobile=mobile,
            is_faculty=True,
            is_active=False  # Set inactive until OTP is verified
        )
        
        FacultyProfile.objects.create(user=user, subject=subject_param)
        
        # Generate OTP
        otp_code = str(random.randint(100000, 999999))
        OTPVerification.objects.create(user=user, otp_code=otp_code)
        
        # Send Email
        subject = 'Verify your Faculty ERP Account'
        message = f'Hello {fullname},\n\nYour OTP for registration is: {otp_code}\n\nThank you.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        
        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        except Exception as e:
            messages.error(request, 'Failed to send OTP email. Please try again later.')
            user.delete() # Revert user creation
            return redirect('faculty_register')
            
        request.session['verification_user_id'] = user.id
        messages.success(request, 'Faculty registration successful. Please verify your email with the OTP sent to you.')
        return redirect('verify_otp')

    return render(request, 'faculty/register.html')

@login_required
def faculty_dashboard(request):
    if not request.user.is_faculty:
        return redirect('login')
    
    profile, created = FacultyProfile.objects.get_or_create(user=request.user)
    
    programs = Program.objects.filter(faculty=request.user)
    batches = Batch.objects.filter(faculty=request.user)
    pending_enrollments = Enrollment.objects.filter(program__faculty=request.user, status='PENDING').count()
    
    # For visualizations
    program_stats = []
    for program in programs:
        count = Enrollment.objects.filter(program=program, status='APPROVED').count()
        program_stats.append({'name': program.name, 'count': count})
        
    batch_stats = []
    for batch in batches:
        count = batch.students.count()
        batch_stats.append({'name': batch.name, 'count': count})
    
    context = {
        'faculty': request.user,
        'profile': profile,
        'programs': programs,
        'batches': batches,
        'pending_enrollments': pending_enrollments,
        'program_stats_json': json.dumps(program_stats),
        'batch_stats_json': json.dumps(batch_stats),
    }
    return render(request, 'faculty/dashboard.html', context)

@login_required
def enrollment_requests(request):
    if not request.user.is_faculty:
        return redirect('login')
        
    enrollments = Enrollment.objects.filter(program__faculty=request.user, status='PENDING')
    
    if request.method == 'POST':
        enrollment_id = request.POST.get('enrollment_id')
        action = request.POST.get('action') # 'approve' or 'reject'
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id, program__faculty=request.user)
            if action == 'approve':
                enrollment.status = 'APPROVED'
            elif action == 'reject':
                enrollment.status = 'REJECTED'
            enrollment.save()
            messages.success(request, f"Enrollment {action}d successfully.")
        except Enrollment.DoesNotExist:
            messages.error(request, "Enrollment not found.")
            
        return redirect('enrollment_requests')
        
    context = {
        'enrollments': enrollments
    }
    return render(request, 'faculty/enrollment_requests.html', context)

@login_required
def batch_management(request):
    if not request.user.is_faculty:
        return redirect('login')
        
    batches = Batch.objects.filter(faculty=request.user)
    programs = Program.objects.filter(faculty=request.user)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        program_id = request.POST.get('program_id')
        try:
            program = Program.objects.get(id=program_id, faculty=request.user)
            Batch.objects.create(name=name, program=program, faculty=request.user)
            messages.success(request, 'Batch created successfully.')
        except Program.DoesNotExist:
            messages.error(request, 'Invalid program selected.')
            
        return redirect('batch_management')
        
    context = {
        'batches': batches,
        'programs': programs
    }
    return render(request, 'faculty/batch_management.html', context)

@login_required
def batch_detail(request, batch_id):
    if not request.user.is_faculty:
        return redirect('login')
        
    try:
        batch = Batch.objects.get(id=batch_id, faculty=request.user)
    except Batch.DoesNotExist:
        messages.error(request, 'Batch not found.')
        return redirect('batch_management')
        
    # Get all students approved in the batch's program
    approved_students = User.objects.filter(
        enrollment__program=batch.program, 
        enrollment__status='APPROVED',
        is_student=True
    ).exclude(batches=batch)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        student_id = request.POST.get('student_id')
        
        try:
            student = User.objects.get(id=student_id, is_student=True)
            if action == 'add':
                batch.students.add(student)
                messages.success(request, 'Student added to batch.')
            elif action == 'remove':
                batch.students.remove(student)
                messages.success(request, 'Student removed from batch.')
        except User.DoesNotExist:
            messages.error(request, 'Student not found.')
            
        return redirect('batch_detail', batch_id=batch.id)
        
    context = {
        'batch': batch,
        'available_students': approved_students
    }
    return render(request, 'faculty/batch_detail.html', context)

@login_required
def mark_attendance(request, batch_id):
    if not request.user.is_faculty:
        return redirect('login')
        
    try:
        batch = Batch.objects.get(id=batch_id, faculty=request.user)
    except Batch.DoesNotExist:
        messages.error(request, 'Batch not found.')
        return redirect('batch_management')
        
    if request.method == 'POST':
        date = request.POST.get('date')
        for student in batch.students.all():
            status = request.POST.get(f'attendance_{student.id}') == 'on'
            Attendance.objects.update_or_create(
                batch=batch,
                student=student,
                date=date,
                defaults={'is_present': status}
            )
        messages.success(request, 'Attendance marked successfully.')
        return redirect('batch_detail', batch_id=batch.id)
        
    context = {'batch': batch}
    return render(request, 'faculty/mark_attendance.html', context)

@login_required
def assignment_management(request):
    if not request.user.is_faculty:
        return redirect('login')
        
    batches = Batch.objects.filter(faculty=request.user)
    
    selected_batch_id = request.GET.get('batch_id')
    if selected_batch_id:
        assignments = Assignment.objects.filter(batch__faculty=request.user, batch_id=selected_batch_id).order_by('-due_date')
    else:
        assignments = Assignment.objects.filter(batch__faculty=request.user).order_by('-due_date')
    
    if request.method == 'POST':
        batch_id = request.POST.get('batch_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        file = request.FILES.get('file')
        
        try:
            batch = Batch.objects.get(id=batch_id, faculty=request.user)
            Assignment.objects.create(
                batch=batch,
                title=title,
                description=description,
                due_date=due_date,
                file=file
            )
            messages.success(request, 'Assignment created successfully.')
        except Batch.DoesNotExist:
            messages.error(request, 'Invalid batch selected.')
            
        # Retain the filter if it was present
        if selected_batch_id:
            return redirect(f"/faculty/assignments/?batch_id={selected_batch_id}")
        return redirect('assignment_management')
        
    context = {
        'batches': batches,
        'assignments': assignments,
        'selected_batch_id': int(selected_batch_id) if selected_batch_id and selected_batch_id.isdigit() else None
    }
    return render(request, 'faculty/assignment_management.html', context)

@login_required
def review_submission(request, submission_id):
    if not request.user.is_faculty:
        return redirect('login')
        
    try:
        submission = AssignmentSubmission.objects.get(id=submission_id, assignment__batch__faculty=request.user)
    except AssignmentSubmission.DoesNotExist:
        messages.error(request, 'Submission not found.')
        return redirect('batch_management')
        
    if request.method == 'POST':
        status = request.POST.get('status') # 'APPROVED' or 'REJECTED'
        feedback = request.POST.get('feedback')
        
        if status in ['APPROVED', 'REJECTED']:
            submission.status = status
            submission.feedback = feedback
            submission.save()
            messages.success(request, 'Submission reviewed successfully.')
        
        return redirect('assignment_management')
        
    context = {'submission': submission}
    return render(request, 'faculty/review_submission.html', context)

@login_required
def create_program(request):
    if not request.user.is_faculty:
        return redirect('login')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        
        if name and subject:
            Program.objects.create(
                name=name,
                subject=subject,
                faculty=request.user
            )
            messages.success(request, 'Program created successfully.')
        else:
            messages.error(request, 'Please provide both program name and subject.')
            
    return redirect('faculty_dashboard')

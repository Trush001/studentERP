from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def index(request):
    return render(request, 'core/index.html')

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_student:
            return redirect('student_dashboard')
        elif request.user.is_faculty:
            return redirect('faculty_dashboard')
        elif request.user.is_administrator or request.user.is_superuser:
            return redirect('/admin/')
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            if user.is_student:
                return redirect('student_dashboard')
            elif user.is_faculty:
                return redirect('faculty_dashboard')
            elif user.is_administrator or user.is_superuser:
                return redirect('/admin/')
            else:
                return redirect('/')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

from .models import User, OTPVerification

def verify_otp(request):
    user_id = request.session.get('verification_user_id')
    if not user_id:
        messages.error(request, 'No active registration found. Please register again.')
        return redirect('login')
        
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        try:
            user = User.objects.get(id=user_id)
            otp_record = OTPVerification.objects.get(user=user)
            
            if otp_record.otp_code == otp_entered:
                user.is_active = True
                user.save()
                otp_record.delete()
                
                # Clear session
                del request.session['verification_user_id']
                
                messages.success(request, 'Email verified successfully. You are now logged in.')
                login(request, user)
                
                if user.is_student:
                    return redirect('student_dashboard')
                elif user.is_faculty:
                    return redirect('faculty_dashboard')
                else:
                    return redirect('/')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
        except (User.DoesNotExist, OTPVerification.DoesNotExist):
            messages.error(request, 'Verification error. Please register again.')
            return redirect('login')
            
    return render(request, 'core/verify_otp.html')

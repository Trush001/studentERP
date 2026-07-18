from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, FacultyProfile

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'fullname', 'is_student', 'is_faculty', 'is_administrator']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Role & Personal Info', {'fields': ('fullname', 'mobile', 'is_student', 'is_faculty', 'is_administrator')}),
    )

class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'enrollment_number', 'course']

class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject']

admin.site.register(User, CustomUserAdmin)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(FacultyProfile, FacultyProfileAdmin)

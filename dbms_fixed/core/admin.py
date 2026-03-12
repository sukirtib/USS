"""
Django Admin configuration for CTLMS.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, StudentProfile, ConsultantProfile, TrainerProfile,
    Course, Batch, CourseRegistration, Enrollment,
    AppointmentBooking, Counseling, MockTest, ExamRegistration,
    Payment, StudentDocument, MockTestScore
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'full_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'role')}),
    )

    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = 'Full Name'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'consultant', 'trainer', 'date_of_birth', 'created_at']
    list_filter = ['consultant', 'trainer']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['consultant', 'trainer']


@admin.register(ConsultantProfile)
class ConsultantProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'created_at']
    search_fields = ['user__username', 'specialization']


@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject_expertise', 'experience_years', 'created_at']
    search_fields = ['user__username', 'subject_expertise']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_name', 'duration_weeks', 'fee', 'is_active']
    list_filter = ['is_active']
    search_fields = ['course_code', 'course_name']


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['batch_code', 'batch_name', 'course', 'trainer', 'start_date', 'status', 'current_students', 'capacity']
    list_filter = ['status', 'course']
    search_fields = ['batch_code', 'batch_name']


@admin.register(CourseRegistration)
class CourseRegistrationAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'batch', 'status', 'registration_date']
    list_filter = ['status']
    search_fields = ['student__user__username', 'course__course_name']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'registration', 'status', 'enrollment_date']
    list_filter = ['status']


@admin.register(AppointmentBooking)
class AppointmentBookingAdmin(admin.ModelAdmin):
    list_display = ['student', 'consultant', 'preferred_date', 'preferred_time', 'status']
    list_filter = ['status']
    search_fields = ['student__user__username', 'consultant__user__username']


@admin.register(Counseling)
class CounselingAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'next_followup', 'created_at']


@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
    list_display = ['mock_test_name', 'course', 'total_marks', 'duration_minutes']


@admin.register(ExamRegistration)
class ExamRegistrationAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'exam_date', 'status', 'score']
    list_filter = ['status']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount', 'purpose', 'payment_method', 'status', 'transaction_id', 'created_at']
    list_filter = ['status', 'purpose', 'payment_method']
    search_fields = ['student__user__username', 'transaction_id']
    readonly_fields = ['transaction_id', 'created_at']


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ['student', 'document_type', 'uploaded_at']


@admin.register(MockTestScore)
class MockTestScoreAdmin(admin.ModelAdmin):
    list_display = ['student', 'mock_test', 'trainer', 'score', 'recorded_at']
    list_filter = ['mock_test', 'trainer']
    search_fields = ['student__user__username', 'mock_test__mock_test_name']

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Student
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile_edit, name='student_profile_edit'),
    path('student/appointments/', views.student_appointments, name='student_appointments'),
    path('student/appointments/book/', views.book_appointment, name='book_appointment'),
    path('student/courses/', views.student_courses, name='student_courses'),
    path('student/courses/register/', views.register_course, name='register_course'),
    path('student/exams/register/', views.register_exam, name='register_exam'),
    path('student/documents/', views.student_documents, name='student_documents'),

    # Consultant
    path('consultant/', views.consultant_dashboard, name='consultant_dashboard'),
    path('consultant/session/<int:appointment_id>/', views.conduct_counseling, name='conduct_counseling'),

    # Trainer
    path('trainer/', views.trainer_dashboard, name='trainer_dashboard'),
    path('trainer/batch/<int:batch_id>/', views.trainer_batch_detail, name='trainer_batch_detail'),
    path('trainer/batch/<int:batch_id>/score/', views.trainer_record_score, name='trainer_record_score'),

    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/approve-registration/<int:reg_id>/', views.admin_approve_registration, name='admin_approve_registration'),
    path('admin-panel/approve-appointment/<int:appointment_id>/', views.admin_approve_appointment, name='admin_approve_appointment'),
    path('admin-panel/approve-exam/<int:exam_id>/', views.admin_approve_exam, name='admin_approve_exam'),
    path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
]

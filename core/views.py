"""
CTLMS Views - Role-based dashboards and CRUD operations.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    User, StudentProfile, ConsultantProfile, TrainerProfile,
    Course, Batch, CourseRegistration, Enrollment,
    AppointmentBooking, Counseling, MockTest, ExamRegistration,
    Payment
)
from .forms import (
    UserRegistrationForm, StudentProfileForm, AppointmentBookingForm,
    CourseRegistrationForm, ExamRegistrationForm, PaymentForm, CounselingSessionForm
)


def is_admin(user):
    return user.is_authenticated and user.role == User.Role.ADMIN


def is_consultant(user):
    return user.is_authenticated and user.role == User.Role.CONSULTANT


def is_trainer(user):
    return user.is_authenticated and user.role == User.Role.TRAINER


def is_student(user):
    return user.is_authenticated and user.role == User.Role.STUDENT


# ============ PUBLIC PAGES ============

def home(request):
    """Landing page."""
    courses = Course.objects.filter(is_active=True)[:6]
    return render(request, 'core/home.html', {'courses': courses})


def login_view(request):
    """User login."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'core/login.html')


def logout_view(request):
    """User logout."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


def register(request):
    """User registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = user.role
            if role == User.Role.STUDENT:
                StudentProfile.objects.create(user=user)
            elif role == User.Role.CONSULTANT:
                ConsultantProfile.objects.create(user=user)
            elif role == User.Role.TRAINER:
                TrainerProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    return render(request, 'core/register.html', {'form': form})


# ============ DASHBOARD ============

@login_required
def dashboard(request):
    """Role-based dashboard redirect."""
    if request.user.role == User.Role.ADMIN:
        return redirect('admin_dashboard')
    elif request.user.role == User.Role.STUDENT:
        return redirect('student_dashboard')
    elif request.user.role == User.Role.CONSULTANT:
        return redirect('consultant_dashboard')
    elif request.user.role == User.Role.TRAINER:
        return redirect('trainer_dashboard')
    return redirect('home')


# ============ STUDENT VIEWS ============

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    """Student dashboard."""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        profile = StudentProfile.objects.create(user=request.user)

    appointments = profile.appointments.order_by('-preferred_date')[:5]
    registrations = profile.course_registrations.order_by('-registration_date')[:5]
    enrollments = profile.enrollments.filter(status='ACTIVE')
    exam_regs = profile.exam_registrations.order_by('-exam_date')[:5]

    context = {
        'profile': profile,
        'appointments': appointments,
        'registrations': registrations,
        'enrollments': enrollments,
        'exam_registrations': exam_regs,
    }
    return render(request, 'core/student/dashboard.html', context)


@login_required
@user_passes_test(is_student)
def student_profile_edit(request):
    """Edit student profile."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('student_dashboard')
    else:
        form = StudentProfileForm(instance=profile)
    return render(request, 'core/student/profile_edit.html', {'form': form})


@login_required
@user_passes_test(is_student)
def book_appointment(request):
    """Book counseling appointment."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    consultants = ConsultantProfile.objects.select_related('user').all()
    if not consultants:
        messages.warning(request, 'No consultants available. Please contact admin.')
        return redirect('student_dashboard')
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.student = profile
            appointment.save()
            messages.success(request, 'Appointment request submitted. You will be notified once approved.')
            return redirect('student_dashboard')
    else:
        form = AppointmentBookingForm()
    return render(request, 'core/student/book_appointment.html', {'form': form, 'consultants': consultants})


@login_required
@user_passes_test(is_student)
def register_course(request):
    """Register for a course."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    courses = Course.objects.filter(is_active=True)
    batches = Batch.objects.filter(status__in=['UPCOMING', 'ONGOING']).select_related('course', 'trainer')

    if request.method == 'POST':
        form = CourseRegistrationForm(request.POST)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.student = profile
            reg.save()
            messages.success(request, 'Course registration submitted. Admin will review and approve.')
            return redirect('student_dashboard')
    else:
        form = CourseRegistrationForm()
    return render(request, 'core/student/register_course.html', {
        'form': form, 'courses': courses, 'batches': batches
    })


@login_required
@user_passes_test(is_student)
def register_exam(request):
    """Register for exam."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    courses = Course.objects.filter(is_active=True)
    mock_tests = MockTest.objects.select_related('course')

    if request.method == 'POST':
        form = ExamRegistrationForm(request.POST)
        if form.is_valid():
            exam_reg = form.save(commit=False)
            exam_reg.student = profile
            exam_reg.fee = exam_reg.course.fee * 0.3  # Example: 30% of course fee for exam
            exam_reg.save()
            messages.success(request, 'Exam registration submitted.')
            return redirect('student_dashboard')
    else:
        form = ExamRegistrationForm()
    return render(request, 'core/student/register_exam.html', {
        'form': form, 'courses': courses, 'mock_tests': mock_tests
    })


@login_required
@user_passes_test(is_student)
def student_appointments(request):
    """List all appointments."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    appointments = profile.appointments.order_by('-preferred_date')
    return render(request, 'core/student/appointments.html', {'appointments': appointments})


@login_required
@user_passes_test(is_student)
def student_courses(request):
    """List registrations and enrollments."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    registrations = profile.course_registrations.order_by('-registration_date')
    enrollments = profile.enrollments.order_by('-enrollment_date')
    return render(request, 'core/student/courses.html', {
        'registrations': registrations, 'enrollments': enrollments
    })


# ============ CONSULTANT VIEWS ============

@login_required
@user_passes_test(is_consultant)
def consultant_dashboard(request):
    """Consultant dashboard."""
    profile = get_object_or_404(ConsultantProfile, user=request.user)
    today = timezone.now().date()
    upcoming = profile.appointments.filter(
        preferred_date__gte=today, status='APPROVED'
    ).order_by('preferred_date', 'preferred_time')[:10]
    pending = profile.appointments.filter(status='PENDING').order_by('preferred_date')
    total_sessions = Counseling.objects.filter(appointment__consultant=profile).count()

    context = {
        'profile': profile,
        'upcoming_appointments': upcoming,
        'pending_appointments': pending,
        'total_sessions': total_sessions,
    }
    return render(request, 'core/consultant/dashboard.html', context)


@login_required
@user_passes_test(is_consultant)
def conduct_counseling(request, appointment_id):
    """Record counseling session."""
    profile = get_object_or_404(ConsultantProfile, user=request.user)
    appointment = get_object_or_404(AppointmentBooking, id=appointment_id, consultant=profile)

    if appointment.status != 'APPROVED' and appointment.status != 'COMPLETED':
        messages.error(request, 'This appointment is not approved for counseling.')
        return redirect('consultant_dashboard')

    if request.method == 'POST':
        form = CounselingSessionForm(request.POST)
        if form.is_valid():
            counseling = form.save(commit=False)
            counseling.appointment = appointment
            counseling.save()
            appointment.status = 'COMPLETED'
            appointment.save()
            messages.success(request, 'Counseling session recorded successfully.')
            return redirect('consultant_dashboard')
    else:
        form = CounselingSessionForm()
    return render(request, 'core/consultant/conduct_counseling.html', {
        'form': form, 'appointment': appointment
    })


# ============ TRAINER VIEWS ============

@login_required
@user_passes_test(is_trainer)
def trainer_dashboard(request):
    """Trainer dashboard."""
    profile = get_object_or_404(TrainerProfile, user=request.user)
    batches = profile.batches.filter(status__in=['UPCOMING', 'ONGOING']).order_by('start_date')
    total_students = sum(b.current_students for b in profile.batches.all())

    context = {
        'profile': profile,
        'batches': batches,
        'total_students': total_students,
    }
    return render(request, 'core/trainer/dashboard.html', context)


@login_required
@user_passes_test(is_trainer)
def trainer_batch_detail(request, batch_id):
    """View batch details and enrolled students."""
    profile = get_object_or_404(TrainerProfile, user=request.user)
    batch = get_object_or_404(Batch, id=batch_id, trainer=profile)
    enrollments = Enrollment.objects.filter(registration__batch=batch, status='ACTIVE')
    return render(request, 'core/trainer/batch_detail.html', {
        'batch': batch, 'enrollments': enrollments
    })


# ============ ADMIN VIEWS ============

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard with reports."""
    stats = {
        'total_students': StudentProfile.objects.count(),
        'total_consultants': ConsultantProfile.objects.count(),
        'total_trainers': TrainerProfile.objects.count(),
        'total_courses': Course.objects.filter(is_active=True).count(),
        'pending_registrations': CourseRegistration.objects.filter(status='PENDING').count(),
        'pending_appointments': AppointmentBooking.objects.filter(status='PENDING').count(),
        'total_revenue': Payment.objects.filter(status='COMPLETED').aggregate(Sum('amount'))['amount__sum'] or 0,
    }

    recent_registrations = CourseRegistration.objects.select_related(
        'student', 'course', 'batch'
    ).order_by('status', '-registration_date')[:10]  # PENDING first (alphabetically)

    recent_appointments = AppointmentBooking.objects.select_related(
        'student', 'consultant'
    ).order_by('status', '-created_at')[:10]

    return render(request, 'core/admin/dashboard.html', {
        'stats': stats,
        'recent_registrations': recent_registrations,
        'recent_appointments': recent_appointments,
    })


@login_required
@user_passes_test(is_admin)
def admin_approve_registration(request, reg_id):
    """Approve or reject course registration."""
    reg = get_object_or_404(CourseRegistration, id=reg_id)
    if reg.status != 'PENDING':
        messages.warning(request, 'This registration has already been processed.')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            reg.status = 'APPROVED'
            reg.approved_by = request.user
            reg.approved_date = timezone.now()
            reg.save()
            Enrollment.objects.create(student=reg.student, registration=reg)
            reg.batch.current_students += 1
            reg.batch.save()
            messages.success(request, 'Registration approved. Student enrolled.')
        elif action == 'reject':
            reg.status = 'REJECTED'
            reg.approved_by = request.user
            reg.approved_date = timezone.now()
            reg.save()
            messages.info(request, 'Registration rejected.')
        return redirect('admin_dashboard')
    return render(request, 'core/admin/approve_registration.html', {'reg': reg})


@login_required
@user_passes_test(is_admin)
def admin_approve_appointment(request, appointment_id):
    """Approve or reject appointment."""
    appointment = get_object_or_404(AppointmentBooking, id=appointment_id)
    if appointment.status != 'PENDING':
        messages.warning(request, 'This appointment has already been processed.')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            appointment.status = 'APPROVED'
            appointment.approved_by = request.user
            appointment.save()
            messages.success(request, 'Appointment approved.')
        elif action == 'reject':
            appointment.status = 'REJECTED'
            appointment.approved_by = request.user
            appointment.save()
            messages.info(request, 'Appointment rejected.')
        return redirect('admin_dashboard')
    return render(request, 'core/admin/approve_appointment.html', {'appointment': appointment})


@login_required
@user_passes_test(is_admin)
def admin_reports(request):
    """Generate reports."""
    course_enrollments = list(Course.objects.annotate(
        enrollment_count=Count('registrations', filter=Q(registrations__status='APPROVED'))
    ).values('course_name', 'enrollment_count'))

    consultant_sessions = [
        {
            'name': f"{cp.user.first_name} {cp.user.last_name}".strip() or cp.user.username,
            'session_count': cp.appointments.filter(status='COMPLETED').count(),
        }
        for cp in ConsultantProfile.objects.select_related('user')
    ]

    financial_summary = Payment.objects.filter(status='COMPLETED').values(
        'purpose'
    ).annotate(total=Sum('amount'))

    purpose_labels = dict(Payment.Purpose.choices)
    financial_summary = [
        {'purpose': purpose_labels.get(f['purpose'], f['purpose']), 'total': f['total']}
        for f in financial_summary
    ]

    return render(request, 'core/admin/reports.html', {
        'course_enrollments': course_enrollments,
        'consultant_sessions': consultant_sessions,
        'financial_summary': financial_summary,
    })
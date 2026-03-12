"""
CTLMS Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from .models import (
    User, StudentProfile, ConsultantProfile, TrainerProfile,
    Course, Batch, CourseRegistration, Enrollment,
    AppointmentBooking, Counseling, MockTest, ExamRegistration,
    Payment, StudentDocument, MockTestScore
)
from .forms import (
    UserRegistrationForm, StudentProfileForm, AppointmentBookingForm,
    CourseRegistrationForm, ExamRegistrationForm, PaymentForm,
    CounselingSessionForm, PaymentSimulationForm, StudentDocumentForm,
    MockTestScoreForm
)


def is_admin(user): return user.is_authenticated and user.role == User.Role.ADMIN
def is_consultant(user): return user.is_authenticated and user.role == User.Role.CONSULTANT
def is_trainer(user): return user.is_authenticated and user.role == User.Role.TRAINER
def is_student(user): return user.is_authenticated and user.role == User.Role.STUDENT


# ── PUBLIC ───────────────────────────────────────────────

def home(request):
    courses = Course.objects.filter(is_active=True)[:6]
    stats = {
        'students': StudentProfile.objects.count(),
        'courses': Course.objects.filter(is_active=True).count(),
        'consultants': ConsultantProfile.objects.count(),
        'trainers': TrainerProfile.objects.count(),
    }
    return render(request, 'core/home.html', {'courses': courses, 'stats': stats})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            StudentProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created! Welcome to CTLMS.')
            return redirect('dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    return render(request, 'core/register.html', {'form': form})


# ── DASHBOARD ────────────────────────────────────────────

@login_required
def dashboard(request):
    role = request.user.role
    if role == User.Role.ADMIN: return redirect('admin_dashboard')
    if role == User.Role.STUDENT: return redirect('student_dashboard')
    if role == User.Role.CONSULTANT: return redirect('consultant_dashboard')
    if role == User.Role.TRAINER: return redirect('trainer_dashboard')
    return redirect('home')


# ── STUDENT ──────────────────────────────────────────────

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        profile = StudentProfile.objects.create(user=request.user)

    context = {
        'profile': profile,
        'appointments': profile.appointments.order_by('-preferred_date')[:5],
        'registrations': profile.course_registrations.order_by('-registration_date')[:5],
        'enrollments': profile.enrollments.filter(status='ACTIVE'),
        'exam_registrations': profile.exam_registrations.order_by('-exam_date')[:5],
        'payments': profile.payments.order_by('-created_at')[:5],
        'documents': profile.documents.order_by('-uploaded_at')[:5],
        'mock_scores': profile.mock_scores.select_related('mock_test__course').order_by('-recorded_at')[:5],
    }
    return render(request, 'core/student/dashboard.html', context)


@login_required
@user_passes_test(is_student)
def student_profile_edit(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('student_dashboard')
    else:
        form = StudentProfileForm(instance=profile)
    return render(request, 'core/student/profile_edit.html', {'form': form})


@login_required
@user_passes_test(is_student)
def book_appointment(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    consultants = ConsultantProfile.objects.select_related('user').all()
    if not consultants:
        messages.warning(request, 'No consultants available.')
        return redirect('student_dashboard')
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.student = profile
            appt.save()
            messages.success(request, 'Appointment request submitted!')
            return redirect('student_dashboard')
    else:
        form = AppointmentBookingForm()
    return render(request, 'core/student/book_appointment.html', {
        'form': form, 'consultants': consultants,
        'today': timezone.now().date().isoformat(),
        'max_date': (timezone.now().date() + timedelta(days=30)).isoformat(),
    })


@login_required
@user_passes_test(is_student)
def register_course(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    courses = Course.objects.filter(is_active=True)
    batches = Batch.objects.filter(status__in=['UPCOMING', 'ONGOING']).select_related('course', 'trainer')

    if request.method == 'POST' and 'step' not in request.POST:
        reg_form = CourseRegistrationForm(request.POST, student=profile)
        if reg_form.is_valid():
            course = reg_form.cleaned_data['course']
            batch = reg_form.cleaned_data['batch']
            request.session['pending_course_id'] = course.id
            request.session['pending_batch_id'] = batch.id
            return render(request, 'core/student/payment_simulation.html', {
                'pay_form': PaymentSimulationForm(), 'course': course, 'batch': batch,
            })
    elif request.method == 'POST' and request.POST.get('step') == 'pay':
        pay_form = PaymentSimulationForm(request.POST)
        course = get_object_or_404(Course, id=request.session.get('pending_course_id'))
        batch = get_object_or_404(Batch, id=request.session.get('pending_batch_id'))
        if pay_form.is_valid():
            reg = CourseRegistration.objects.create(student=profile, course=course, batch=batch)
            txn_id = str(uuid.uuid4()).replace('-', '').upper()[:16]
            Payment.objects.create(
                student=profile, amount=course.fee,
                payment_method=pay_form.cleaned_data['payment_method'],
                purpose=Payment.Purpose.COURSE_FEE,
                status=Payment.Status.COMPLETED, transaction_id=txn_id,
            )
            request.session.pop('pending_course_id', None)
            request.session.pop('pending_batch_id', None)
            messages.success(request, f'Payment of ₹{course.fee} confirmed (TXN: {txn_id}). Registration pending approval.')
            return redirect('student_dashboard')
        return render(request, 'core/student/payment_simulation.html', {
            'pay_form': pay_form, 'course': course, 'batch': batch,
        })
    else:
        reg_form = CourseRegistrationForm(student=profile)

    return render(request, 'core/student/register_course.html', {
        'form': reg_form, 'courses': courses, 'batches': batches
    })


@login_required
@user_passes_test(is_student)
def register_exam(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == 'POST':
        form = ExamRegistrationForm(request.POST)
        if form.is_valid():
            exam_reg = form.save(commit=False)
            exam_reg.student = profile
            exam_reg.fee = exam_reg.course.fee * Decimal('0.3')
            exam_reg.save()
            messages.success(request, 'Exam registration submitted.')
            return redirect('student_dashboard')
    else:
        form = ExamRegistrationForm()
    return render(request, 'core/student/register_exam.html', {
        'form': form,
        'courses': Course.objects.filter(is_active=True),
        'mock_tests': MockTest.objects.select_related('course'),
    })


@login_required
@user_passes_test(is_student)
def student_appointments(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    return render(request, 'core/student/appointments.html', {
        'appointments': profile.appointments.order_by('-preferred_date')
    })


@login_required
@user_passes_test(is_student)
def student_courses(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    return render(request, 'core/student/courses.html', {
        'registrations': profile.course_registrations.order_by('-registration_date'),
        'enrollments': profile.enrollments.order_by('-enrollment_date'),
    })


@login_required
@user_passes_test(is_student)
def student_documents(request):
    """Upload and view documents."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == 'POST':
        form = StudentDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.student = profile
            doc.save()
            messages.success(request, 'Document uploaded successfully.')
            return redirect('student_documents')
    else:
        form = StudentDocumentForm()
    return render(request, 'core/student/documents.html', {
        'form': form, 'documents': profile.documents.order_by('-uploaded_at')
    })


# ── CONSULTANT ───────────────────────────────────────────

@login_required
@user_passes_test(is_consultant)
def consultant_dashboard(request):
    profile = get_object_or_404(ConsultantProfile, user=request.user)
    today = timezone.now().date()
    context = {
        'profile': profile,
        'upcoming_appointments': profile.appointments.filter(preferred_date__gte=today, status='APPROVED').order_by('preferred_date', 'preferred_time')[:10],
        'pending_appointments': profile.appointments.filter(status='PENDING').order_by('preferred_date'),
        'total_sessions': Counseling.objects.filter(appointment__consultant=profile).count(),
        'assigned_students': profile.students.select_related('user').order_by('user__first_name'),
    }
    return render(request, 'core/consultant/dashboard.html', context)


@login_required
@user_passes_test(is_consultant)
def conduct_counseling(request, appointment_id):
    profile = get_object_or_404(ConsultantProfile, user=request.user)
    appointment = get_object_or_404(AppointmentBooking, id=appointment_id, consultant=profile)
    if appointment.status not in ['APPROVED', 'COMPLETED']:
        messages.error(request, 'Appointment not approved.')
        return redirect('consultant_dashboard')
    if request.method == 'POST':
        form = CounselingSessionForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.appointment = appointment
            c.save()
            appointment.status = 'COMPLETED'
            appointment.save()
            messages.success(request, 'Session recorded.')
            return redirect('consultant_dashboard')
    else:
        form = CounselingSessionForm()
    return render(request, 'core/consultant/conduct_counseling.html', {'form': form, 'appointment': appointment})


# ── TRAINER ──────────────────────────────────────────────

@login_required
@user_passes_test(is_trainer)
def trainer_dashboard(request):
    profile = get_object_or_404(TrainerProfile, user=request.user)
    batches = profile.batches.filter(status__in=['UPCOMING', 'ONGOING']).order_by('start_date')
    context = {
        'profile': profile,
        'batches': batches,
        'total_students': sum(b.current_students for b in profile.batches.all()),
        'assigned_students': profile.students.select_related('user').order_by('user__first_name'),
        'recent_scores': profile.recorded_scores.select_related('student__user', 'mock_test').order_by('-recorded_at')[:10],
    }
    return render(request, 'core/trainer/dashboard.html', context)


@login_required
@user_passes_test(is_trainer)
def trainer_batch_detail(request, batch_id):
    profile = get_object_or_404(TrainerProfile, user=request.user)
    batch = get_object_or_404(Batch, id=batch_id, trainer=profile)
    enrollments = Enrollment.objects.filter(registration__batch=batch, status='ACTIVE').select_related('student__user')
    mock_tests = MockTest.objects.filter(course=batch.course)
    return render(request, 'core/trainer/batch_detail.html', {
        'batch': batch, 'enrollments': enrollments, 'mock_tests': mock_tests
    })


@login_required
@user_passes_test(is_trainer)
def trainer_record_score(request, batch_id):
    """Trainer records mock test score for a student."""
    profile = get_object_or_404(TrainerProfile, user=request.user)
    batch = get_object_or_404(Batch, id=batch_id, trainer=profile)
    enrollments = Enrollment.objects.filter(registration__batch=batch, status='ACTIVE').select_related('student__user')
    mock_tests = MockTest.objects.filter(course=batch.course)

    if request.method == 'POST':
        form = MockTestScoreForm(request.POST, batch=batch)
        if form.is_valid():
            score_obj, created = MockTestScore.objects.update_or_create(
                student=form.cleaned_data['student'],
                mock_test=form.cleaned_data['mock_test'],
                defaults={
                    'trainer': profile,
                    'score': form.cleaned_data['score'],
                    'remarks': form.cleaned_data['remarks'],
                }
            )
            messages.success(request, f'Score recorded for {score_obj.student.user.get_full_name()}.')
            return redirect('trainer_batch_detail', batch_id=batch_id)
    else:
        form = MockTestScoreForm(batch=batch)

    return render(request, 'core/trainer/record_score.html', {
        'form': form, 'batch': batch, 'enrollments': enrollments, 'mock_tests': mock_tests
    })


# ── ADMIN ────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    stats = {
        'total_students': StudentProfile.objects.count(),
        'total_consultants': ConsultantProfile.objects.count(),
        'total_trainers': TrainerProfile.objects.count(),
        'total_courses': Course.objects.filter(is_active=True).count(),
        'pending_registrations': CourseRegistration.objects.filter(status='PENDING').count(),
        'pending_appointments': AppointmentBooking.objects.filter(status='PENDING').count(),
        'pending_exams': ExamRegistration.objects.filter(status='PENDING').count(),
        'total_revenue': Payment.objects.filter(status='COMPLETED').aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    return render(request, 'core/admin/dashboard.html', {
        'stats': stats,
        'recent_registrations': CourseRegistration.objects.select_related('student', 'course', 'batch').order_by('status', '-registration_date')[:10],
        'recent_appointments': AppointmentBooking.objects.select_related('student', 'consultant').order_by('status', '-created_at')[:10],
        'recent_exams': ExamRegistration.objects.select_related('student', 'course').order_by('status', '-created_at')[:10],
        'recent_payments': Payment.objects.select_related('student').order_by('-created_at')[:10],
    })


@login_required
@user_passes_test(is_admin)
def admin_approve_registration(request, reg_id):
    reg = get_object_or_404(CourseRegistration, id=reg_id)
    if reg.status != 'PENDING':
        messages.warning(request, 'Already processed.')
        return redirect('admin_dashboard')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            reg.status = 'APPROVED'
            reg.approved_by = request.user
            reg.approved_date = timezone.now()
            reg.save()
            enrollment = Enrollment.objects.create(student=reg.student, registration=reg, batch=reg.batch)
            Payment.objects.filter(student=reg.student, purpose=Payment.Purpose.COURSE_FEE, enrollment__isnull=True).filter(created_at__gte=reg.created_at).update(enrollment=enrollment)
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
    appointment = get_object_or_404(AppointmentBooking, id=appointment_id)
    if appointment.status != 'PENDING':
        messages.warning(request, 'Already processed.')
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
def admin_approve_exam(request, exam_id):
    """Admin approves or rejects exam registration."""
    exam = get_object_or_404(ExamRegistration, id=exam_id)
    if exam.status != 'PENDING':
        messages.warning(request, 'Already processed.')
        return redirect('admin_dashboard')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            exam.status = 'APPROVED'
            exam.approved_by = request.user
            exam.approved_date = timezone.now()
            exam.save()
            messages.success(request, 'Exam registration approved.')
        elif action == 'reject':
            exam.status = 'REJECTED'
            exam.approved_by = request.user
            exam.approved_date = timezone.now()
            exam.save()
            messages.info(request, 'Exam registration rejected.')
        return redirect('admin_dashboard')
    return render(request, 'core/admin/approve_exam.html', {'exam': exam})


@login_required
@user_passes_test(is_admin)
def admin_reports(request):
    # Course enrollments
    course_enrollments = list(Course.objects.annotate(
        enrollment_count=Count('registrations', filter=Q(registrations__status='APPROVED'))
    ).values('course_name', 'enrollment_count'))

    # Consultant performance
    consultant_sessions = [
        {
            'name': f"{cp.user.first_name} {cp.user.last_name}".strip() or cp.user.username,
            'session_count': cp.appointments.filter(status='COMPLETED').count(),
            'pending_count': cp.appointments.filter(status='PENDING').count(),
            'student_count': cp.students.count(),
        }
        for cp in ConsultantProfile.objects.select_related('user')
    ]

    # Trainer workload
    trainer_workload = [
        {
            'name': f"{tp.user.first_name} {tp.user.last_name}".strip() or tp.user.username,
            'batch_count': tp.batches.count(),
            'active_batches': tp.batches.filter(status__in=['UPCOMING', 'ONGOING']).count(),
            'student_count': sum(b.current_students for b in tp.batches.all()),
            'scores_recorded': tp.recorded_scores.count(),
        }
        for tp in TrainerProfile.objects.select_related('user')
    ]

    # Financial
    purpose_labels = dict(Payment.Purpose.choices)
    financial_summary = [
        {'purpose': purpose_labels.get(f['purpose'], f['purpose']), 'total': f['total']}
        for f in Payment.objects.filter(status='COMPLETED').values('purpose').annotate(total=Sum('amount'))
    ]

    # Student journey / conversion analytics
    total_appointments = AppointmentBooking.objects.count()
    appointments_to_registration = CourseRegistration.objects.count()
    registrations_to_enrollment = Enrollment.objects.count()
    conversion_rate = round((registrations_to_enrollment / appointments_to_registration * 100), 1) if appointments_to_registration else 0

    # Student journeys
    student_journeys = []
    for sp in StudentProfile.objects.select_related('user').prefetch_related(
        'appointments', 'course_registrations', 'enrollments', 'payments'
    )[:20]:
        student_journeys.append({
            'name': sp.user.get_full_name() or sp.user.username,
            'appointments': sp.appointments.count(),
            'registrations': sp.course_registrations.count(),
            'enrollments': sp.enrollments.count(),
            'payments': sp.payments.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0,
        })

    return render(request, 'core/admin/reports.html', {
        'course_enrollments': course_enrollments,
        'consultant_sessions': consultant_sessions,
        'trainer_workload': trainer_workload,
        'financial_summary': financial_summary,
        'conversion_rate': conversion_rate,
        'total_appointments': total_appointments,
        'appointments_to_registration': appointments_to_registration,
        'registrations_to_enrollment': registrations_to_enrollment,
        'student_journeys': student_journeys,
    })

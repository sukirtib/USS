"""
CTLMS Models - Consultancy, Training, and Learning Management System
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        STUDENT = 'STUDENT', 'Student'
        CONSULTANT = 'CONSULTANT', 'Consultant'
        TRAINER = 'TRAINER', 'Trainer'

    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    @property
    def is_admin(self): return self.role == self.Role.ADMIN
    @property
    def is_student(self): return self.role == self.Role.STUDENT
    @property
    def is_consultant(self): return self.role == self.Role.CONSULTANT
    @property
    def is_trainer(self): return self.role == self.Role.TRAINER


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    consultant = models.ForeignKey('ConsultantProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    trainer = models.ForeignKey('TrainerProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return str(self.user)


class ConsultantProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='consultant_profile')
    specialization = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return str(self.user)


class TrainerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trainer_profile')
    subject_expertise = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return str(self.user)


class Course(models.Model):
    course_code = models.CharField(max_length=20, unique=True)
    course_name = models.CharField(max_length=200)
    duration_weeks = models.PositiveIntegerField(default=12)
    fee = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['course_name']

    def __str__(self): return f"{self.course_code} - {self.course_name}"


class Batch(models.Model):
    class Status(models.TextChoices):
        UPCOMING = 'UPCOMING', 'Upcoming'
        ONGOING = 'ONGOING', 'Ongoing'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='batches')
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='batches')
    batch_name = models.CharField(max_length=100)
    batch_code = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(default=30)
    current_students = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = 'Batches'

    def __str__(self): return f"{self.batch_code} - {self.batch_name}"

    @property
    def is_available(self):
        return self.current_students < self.capacity and self.status in [self.Status.UPCOMING, self.Status.ONGOING]


class CourseRegistration(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='course_registrations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='registrations')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_registrations')
    approved_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-registration_date']

    def __str__(self): return f"{self.student} - {self.course} ({self.status})"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        DROPPED = 'DROPPED', 'Dropped'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
    registration = models.OneToOneField(CourseRegistration, on_delete=models.CASCADE, related_name='enrollment')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    certificate_issued = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-enrollment_date']

    def __str__(self): return f"{self.student} - {self.registration.course}"


class AppointmentBooking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='appointments')
    consultant = models.ForeignKey(ConsultantProfile, on_delete=models.CASCADE, related_name='appointments')
    purpose = models.TextField()
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_appointments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-preferred_date', '-preferred_time']

    def __str__(self): return f"{self.student} with {self.consultant} on {self.preferred_date}"


class Counseling(models.Model):
    appointment = models.OneToOneField(AppointmentBooking, on_delete=models.CASCADE, related_name='counseling_session')
    notes = models.TextField(blank=True)
    next_followup = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Counseling sessions'

    def __str__(self): return f"Session for {self.appointment}"


class MockTest(models.Model):
    mock_test_name = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='mock_tests')
    total_marks = models.PositiveIntegerField(default=100)
    duration_minutes = models.PositiveIntegerField(default=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['mock_test_name']

    def __str__(self): return f"{self.mock_test_name} ({self.course})"


class ExamRegistration(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        COMPLETED = 'COMPLETED', 'Completed'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='exam_registrations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exam_registrations')
    mock_test = models.ForeignKey(MockTest, on_delete=models.CASCADE, null=True, blank=True, related_name='registrations')
    exam_date = models.DateField()
    fee = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_exams')
    approved_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-exam_date']

    def __str__(self): return f"{self.student} - {self.course} exam on {self.exam_date}"


class Payment(models.Model):
    class Purpose(models.TextChoices):
        COURSE_FEE = 'COURSE_FEE', 'Course Fee'
        EXAM_FEE = 'EXAM_FEE', 'Exam Registration Fee'
        CONSULTANCY = 'CONSULTANCY', 'Consultancy Service'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        CARD = 'CARD', 'Card'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        ONLINE = 'ONLINE', 'Online'

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='payments')
    exam_registration = models.ForeignKey(ExamRegistration, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self): return f"{self.student} - {self.amount} ({self.purpose})"


class StudentDocument(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=100)
    file = models.FileField(upload_to='student_docs/%Y/%m/')
    description = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.student} - {self.document_type}"


class MockTestScore(models.Model):
    """Trainer-recorded scores for students on mock tests."""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mock_scores')
    mock_test = models.ForeignKey(MockTest, on_delete=models.CASCADE, related_name='scores')
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='recorded_scores')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    remarks = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'mock_test')
        ordering = ['-recorded_at']

    def __str__(self): return f"{self.student} — {self.mock_test}: {self.score}"

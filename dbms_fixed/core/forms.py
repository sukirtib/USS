"""
Forms for CTLMS.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from datetime import timedelta, time
from .models import (
    User, StudentProfile, ConsultantProfile, TrainerProfile,
    Course, Batch, CourseRegistration, AppointmentBooking,
    StudentDocument, MockTest, MockTestScore,
    ExamRegistration, Payment, Counseling
)


class UserRegistrationForm(UserCreationForm):
    """User registration - students only. Role is fixed to STUDENT."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT  # Always student from public registration
        if commit:
            user.save()
        return user


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['date_of_birth', 'address']


class AppointmentBookingForm(forms.ModelForm):
    class Meta:
        model = AppointmentBooking
        fields = ['consultant', 'purpose', 'preferred_date', 'preferred_time', 'duration_minutes']
        widgets = {
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
            'preferred_time': forms.TimeInput(attrs={'type': 'time'}),
            'purpose': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_preferred_date(self):
        date = self.cleaned_data.get('preferred_date')
        if date:
            today = timezone.now().date()
            max_date = today + timedelta(days=30)
            if date < today:
                raise forms.ValidationError('Appointment date cannot be in the past.')
            if date > max_date:
                raise forms.ValidationError('Appointment date must be within the next 30 days.')
        return date

    def clean_preferred_time(self):
        t = self.cleaned_data.get('preferred_time')
        if t:
            start = time(10, 0)   # 10:00 AM
            end = time(17, 0)     # 5:00 PM
            if t < start or t >= end:
                raise forms.ValidationError('Appointment time must be between 10:00 AM and 5:00 PM.')
        return t

    def clean(self):
        cleaned = super().clean()
        consultant = cleaned.get('consultant')
        preferred_date = cleaned.get('preferred_date')
        preferred_time = cleaned.get('preferred_time')
        duration = cleaned.get('duration_minutes', 60)

        if consultant and preferred_date and preferred_time:
            from datetime import datetime, timedelta as td
            existing = AppointmentBooking.objects.filter(
                consultant=consultant,
                preferred_date=preferred_date,
                status__in=['PENDING', 'APPROVED']
            )
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            new_start = datetime.combine(preferred_date, preferred_time)
            new_end = new_start + td(minutes=duration or 60)

            for appt in existing:
                existing_start = datetime.combine(appt.preferred_date, appt.preferred_time)
                existing_end = existing_start + td(minutes=appt.duration_minutes or 60)
                if new_start < existing_end and new_end > existing_start:
                    raise forms.ValidationError(
                        'This consultant is already booked at that time. '
                        'Please choose a different time slot.'
                    )
        return cleaned


class CourseRegistrationForm(forms.ModelForm):
    class Meta:
        model = CourseRegistration
        fields = ['course', 'batch']

    def __init__(self, *args, student=None, **kwargs):
        self.student = student
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        course = cleaned.get('course')
        batch = cleaned.get('batch')
        if course and batch and batch.course_id != course.id:
            raise forms.ValidationError('Selected batch does not belong to the selected course.')
        if batch and not batch.is_available:
            raise forms.ValidationError('This batch is full or not available.')
        if self.student and course:
            already_registered = CourseRegistration.objects.filter(
                student=self.student,
                course=course,
                status__in=['PENDING', 'APPROVED']
            ).exists()
            if already_registered:
                raise forms.ValidationError(
                    'You have already registered or enrolled in this course.'
                )
        return cleaned


class ExamRegistrationForm(forms.ModelForm):
    class Meta:
        model = ExamRegistration
        fields = ['course', 'mock_test', 'exam_date']
        widgets = {
            'exam_date': forms.DateInput(attrs={'type': 'date'}),
        }


class PaymentSimulationForm(forms.Form):
    """Simulated payment form shown to students during course registration."""
    PAYMENT_METHOD_CHOICES = [
        ('CARD', 'Credit / Debit Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('ONLINE', 'Online Wallet'),
        ('CASH', 'Cash'),
    ]
    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES)
    card_number = forms.CharField(
        max_length=19, required=False,
        widget=forms.TextInput(attrs={'placeholder': '1234 5678 9012 3456', 'maxlength': '19'})
    )
    card_holder = forms.CharField(max_length=100, required=False,
                                  widget=forms.TextInput(attrs={'placeholder': 'Name on card'}))
    expiry = forms.CharField(max_length=5, required=False,
                             widget=forms.TextInput(attrs={'placeholder': 'MM/YY'}))
    cvv = forms.CharField(max_length=3, required=False,
                          widget=forms.PasswordInput(attrs={'placeholder': 'CVV'}))


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'purpose', 'transaction_id']


class CounselingSessionForm(forms.ModelForm):
    class Meta:
        model = Counseling
        fields = ['notes', 'next_followup']
        widgets = {
            'next_followup': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 5}),
        }


class StudentDocumentForm(forms.ModelForm):
    class Meta:
        model = StudentDocument
        fields = ['document_type', 'file', 'description']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Optional description'}),
        }


class MockTestScoreForm(forms.Form):
    student = forms.ModelChoiceField(queryset=StudentProfile.objects.none())
    mock_test = forms.ModelChoiceField(queryset=MockTest.objects.none())
    score = forms.DecimalField(max_digits=5, decimal_places=2, min_value=0)
    remarks = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)

    def __init__(self, *args, batch=None, **kwargs):
        super().__init__(*args, **kwargs)
        if batch:
            enrolled_students = StudentProfile.objects.filter(
                enrollments__registration__batch=batch,
                enrollments__status='ACTIVE'
            )
            self.fields['student'].queryset = enrolled_students.distinct()
            self.fields['mock_test'].queryset = MockTest.objects.filter(course=batch.course)

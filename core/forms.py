"""
Forms for CTLMS.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import (
    User, StudentProfile, ConsultantProfile, TrainerProfile,
    Course, Batch, CourseRegistration, AppointmentBooking,
    ExamRegistration, Payment, Counseling
)


class UserRegistrationForm(UserCreationForm):
    """User registration with role selection."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(
        choices=[(r, l) for r, l in User.Role.choices if r != User.Role.ADMIN],
        initial=User.Role.STUDENT
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'password1', 'password2']


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


class CourseRegistrationForm(forms.ModelForm):
    class Meta:
        model = CourseRegistration
        fields = ['course', 'batch']

    def clean(self):
        cleaned = super().clean()
        course = cleaned.get('course')
        batch = cleaned.get('batch')
        if course and batch and batch.course_id != course.id:
            raise forms.ValidationError('Selected batch does not belong to the selected course.')
        if batch and not batch.is_available:
            raise forms.ValidationError('This batch is full or not available.')
        return cleaned


class ExamRegistrationForm(forms.ModelForm):
    class Meta:
        model = ExamRegistration
        fields = ['course', 'mock_test', 'exam_date']
        widgets = {
            'exam_date': forms.DateInput(attrs={'type': 'date'}),
        }


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

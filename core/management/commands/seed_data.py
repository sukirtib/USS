"""
Seed demo data for CTLMS.
Run: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, time, timedelta
from core.models import (
    User, StudentProfile, ConsultantProfile, TrainerProfile,
    Course, Batch, CourseRegistration, MockTest
)


class Command(BaseCommand):
    help = 'Seed demo data for CTLMS'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')

        # Admin
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@ctlms.com', 'admin123',
                first_name='Admin', last_name='User')
            admin.role = 'ADMIN'
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))

        # Consultant
        if not User.objects.filter(username='consultant1').exists():
            cu = User.objects.create_user('consultant1', 'c@ctlms.com', 'pass123',
                first_name='Jane', last_name='Consultant', role='CONSULTANT')
            ConsultantProfile.objects.create(user=cu, specialization='Study Abroad & Career')
            self.stdout.write(self.style.SUCCESS('Created consultant'))

        # Trainer
        if not User.objects.filter(username='trainer1').exists():
            tu = User.objects.create_user('trainer1', 't@ctlms.com', 'pass123',
                first_name='John', last_name='Trainer', role='TRAINER')
            trainer = TrainerProfile.objects.create(user=tu, subject_expertise='English', experience_years=5)

            # Courses
            for code, name, fee in [('IELTS', 'IELTS Preparation', 25000), ('PTE', 'PTE Academic', 20000), ('SAT', 'SAT Prep', 30000)]:
                if not Course.objects.filter(course_code=code).exists():
                    course = Course.objects.create(course_code=code, course_name=name, fee=fee, duration_weeks=12)
                    Batch.objects.create(
                        course=course, trainer=trainer,
                        batch_name=f'{name} Batch A', batch_code=f'{code}-A1',
                        start_date=date.today() + timedelta(days=14),
                        end_date=date.today() + timedelta(days=98),
                        start_time=time(9, 0), end_time=time(11, 0),
                        capacity=20, status='UPCOMING'
                    )
                    MockTest.objects.create(mock_test_name=f'{code} Mock 1', course=course, total_marks=100, duration_minutes=120)
            self.stdout.write(self.style.SUCCESS('Created trainer and courses'))

        # Student
        if not User.objects.filter(username='student1').exists():
            su = User.objects.create_user('student1', 's@ctlms.com', 'pass123',
                first_name='Alex', last_name='Student', role='STUDENT')
            StudentProfile.objects.create(user=su, date_of_birth=date(2000, 5, 15))
            self.stdout.write(self.style.SUCCESS('Created student'))

        self.stdout.write(self.style.SUCCESS('Done! Login: admin/admin123, student1/pass123, consultant1/pass123, trainer1/pass123'))

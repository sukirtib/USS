"""
Seed demo data for CTLMS.
Run: python manage.py seed_data
Run with --force to reset and reseed: python manage.py seed_data --force
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, time, timedelta
from decimal import Decimal
import uuid
from core.models import (
    User, StudentProfile, ConsultantProfile, TrainerProfile,
    Course, Batch, CourseRegistration, MockTest, Enrollment,
    AppointmentBooking, Counseling, ExamRegistration, Payment, MockTestScore
)


class Command(BaseCommand):
    help = 'Seed demo data for CTLMS'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Delete existing data and reseed')

    def handle(self, *args, **options):
        # Always update admin privileges
        admin_user = User.objects.filter(username='admin').first()
        if admin_user and (not admin_user.is_staff or not admin_user.is_superuser):
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Updated admin with superuser privileges'))

        if options['force']:
            self.stdout.write('Force flag set - clearing demo data...')
            # Delete demo data (but keep admin user)
            MockTestScore.objects.all().delete()
            Payment.objects.all().delete()
            ExamRegistration.objects.all().delete()
            Counseling.objects.all().delete()
            AppointmentBooking.objects.all().delete()
            Enrollment.objects.all().delete()
            CourseRegistration.objects.all().delete()
            MockTest.objects.all().delete()
            Batch.objects.all().delete()
            Course.objects.all().delete()
            StudentProfile.objects.all().delete()
            TrainerProfile.objects.all().delete()
            ConsultantProfile.objects.all().delete()
            User.objects.exclude(username='admin').delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing demo data'))
        elif User.objects.filter(username='student1').exists():
            self.stdout.write(self.style.WARNING('Demo data already seeded. Use --force to reseed.'))
            return
        self.stdout.write('Seeding data...')

        # Admin
        if not admin_user:
            admin = User.objects.create_superuser('admin', 'admin@ctlms.com', 'admin123',
                first_name='Admin', last_name='User')
            admin.role = 'ADMIN'
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))

        # Multiple Consultants
        consultants = []
        consultant_data = [
            ('consultant1', 'Jane', 'Wilson', 'Study Abroad & Career Counseling'),
            ('consultant2', 'Robert', 'Brown', 'University Admissions'),
            ('consultant3', 'Sarah', 'Davis', 'Visa & Immigration'),
        ]
        for username, first, last, spec in consultant_data:
            if not User.objects.filter(username=username).exists():
                cu = User.objects.create_user(username, f'{username}@ctlms.com', 'pass123',
                    first_name=first, last_name=last, role='CONSULTANT')
                cp = ConsultantProfile.objects.create(user=cu, specialization=spec)
                consultants.append(cp)
        self.stdout.write(self.style.SUCCESS(f'Created {len(consultant_data)} consultants'))

        # Multiple Trainers
        trainers = []
        trainer_data = [
            ('trainer1', 'John', 'Smith', 'IELTS & English', 8),
            ('trainer2', 'Emily', 'Johnson', 'PTE & Academic Writing', 5),
            ('trainer3', 'Michael', 'Lee', 'SAT & GRE', 10),
        ]
        for username, first, last, expertise, years in trainer_data:
            if not User.objects.filter(username=username).exists():
                tu = User.objects.create_user(username, f'{username}@ctlms.com', 'pass123',
                    first_name=first, last_name=last, role='TRAINER')
                tp = TrainerProfile.objects.create(user=tu, subject_expertise=expertise, experience_years=years)
                trainers.append(tp)
        self.stdout.write(self.style.SUCCESS(f'Created {len(trainer_data)} trainers'))

        # Courses with multiple batches
        courses = []
        course_data = [
            ('IELTS', 'IELTS Preparation', 25000, 12, 'Complete IELTS preparation covering all four modules'),
            ('PTE', 'PTE Academic', 20000, 10, 'PTE Academic test preparation with practice tests'),
            ('SAT', 'SAT Preparation', 30000, 14, 'Comprehensive SAT prep for Math and English'),
            ('GRE', 'GRE Graduate Prep', 35000, 16, 'GRE preparation for graduate school admission'),
            ('TOEFL', 'TOEFL iBT', 22000, 10, 'TOEFL internet-based test preparation'),
        ]
        for code, name, fee, weeks, desc in course_data:
            if not Course.objects.filter(course_code=code).exists():
                course = Course.objects.create(
                    course_code=code, course_name=name, fee=fee, 
                    duration_weeks=weeks, description=desc
                )
                courses.append(course)
                # Create multiple batches per course
                trainer = TrainerProfile.objects.first()
                for i, (status, days_offset) in enumerate([('ONGOING', -30), ('UPCOMING', 14), ('UPCOMING', 45)]):
                    Batch.objects.create(
                        course=course, trainer=trainer,
                        batch_name=f'{name} Batch {chr(65+i)}', batch_code=f'{code}-{chr(65+i)}1',
                        start_date=date.today() + timedelta(days=days_offset),
                        end_date=date.today() + timedelta(days=days_offset + weeks*7),
                        start_time=time(9 + i*2, 0), end_time=time(11 + i*2, 0),
                        capacity=20, current_students=5 if status == 'ONGOING' else 0,
                        status=status
                    )
                # Mock tests
                for j in range(1, 4):
                    MockTest.objects.create(
                        mock_test_name=f'{code} Mock Test {j}', 
                        course=course, total_marks=100, duration_minutes=120
                    )
        self.stdout.write(self.style.SUCCESS(f'Created {len(course_data)} courses with batches'))

        # Multiple Students with various states
        student_data = [
            ('student1', 'Alex', 'Thompson', date(2000, 5, 15)),
            ('student2', 'Emma', 'Garcia', date(2001, 3, 22)),
            ('student3', 'James', 'Martinez', date(1999, 8, 10)),
            ('student4', 'Sophia', 'Anderson', date(2002, 1, 5)),
            ('student5', 'Liam', 'Taylor', date(2000, 11, 18)),
            ('student6', 'Olivia', 'Thomas', date(2001, 7, 30)),
            ('student7', 'Noah', 'Jackson', date(1998, 12, 25)),
            ('student8', 'Ava', 'White', date(2003, 4, 12)),
        ]
        students = []
        consultant = ConsultantProfile.objects.first()
        trainer = TrainerProfile.objects.first()
        for username, first, last, dob in student_data:
            if not User.objects.filter(username=username).exists():
                su = User.objects.create_user(username, f'{username}@ctlms.com', 'pass123',
                    first_name=first, last_name=last, role='STUDENT')
                sp = StudentProfile.objects.create(
                    user=su, date_of_birth=dob, 
                    consultant=consultant, trainer=trainer,
                    address=f'{100 + len(students)} Main Street, City'
                )
                students.append(sp)
        self.stdout.write(self.style.SUCCESS(f'Created {len(student_data)} students'))

        # Course Registrations (various statuses)
        courses = list(Course.objects.all())
        batches = list(Batch.objects.all())
        students = list(StudentProfile.objects.all())
        
        registrations_created = 0
        for i, student in enumerate(students[:6]):
            course = courses[i % len(courses)]
            batch = Batch.objects.filter(course=course).first()
            status = ['PENDING', 'APPROVED', 'APPROVED', 'PENDING', 'REJECTED', 'APPROVED'][i]
            reg = CourseRegistration.objects.create(
                student=student, course=course, batch=batch, status=status
            )
            registrations_created += 1
            # Create enrollment for approved registrations
            if status == 'APPROVED':
                Enrollment.objects.create(
                    student=student, registration=reg, batch=batch,
                    status='ACTIVE', enrollment_date=timezone.now()
                )
            # Create payment for some
            if i < 4:
                Payment.objects.create(
                    student=student, amount=course.fee,
                    payment_method='CARD' if i % 2 == 0 else 'BANK',
                    purpose='COURSE_FEE', status='COMPLETED',
                    transaction_id=str(uuid.uuid4()).replace('-', '').upper()[:16]
                )
        self.stdout.write(self.style.SUCCESS(f'Created {registrations_created} course registrations'))

        # Appointments (various statuses)
        consultants = list(ConsultantProfile.objects.all())
        appointments_created = 0
        for i, student in enumerate(students[:5]):
            consultant = consultants[i % len(consultants)]
            status = ['PENDING', 'APPROVED', 'COMPLETED', 'PENDING', 'CANCELLED'][i]
            apt = AppointmentBooking.objects.create(
                student=student, consultant=consultant,
                preferred_date=date.today() + timedelta(days=i*2 - 2),
                preferred_time=time(10 + i, 0),
                purpose=f'Career counseling session #{i+1}',
                status=status
            )
            appointments_created += 1
            # Create counseling record for completed appointments
            if status == 'COMPLETED':
                Counseling.objects.create(
                    appointment=apt,
                    recommendations='Recommended IELTS preparation, target universities shortlisted.',
                    notes='Student shows good progress. Follow up in 2 weeks.',
                    next_followup=date.today() + timedelta(days=14)
                )
        self.stdout.write(self.style.SUCCESS(f'Created {appointments_created} appointments'))

        # Exam Registrations
        exams_created = 0
        for i, student in enumerate(students[:4]):
            course = courses[i % len(courses)]
            status = ['PENDING', 'APPROVED', 'COMPLETED', 'PENDING'][i]
            exam = ExamRegistration.objects.create(
                student=student, course=course,
                exam_date=date.today() + timedelta(days=30 + i*7),
                fee=course.fee * Decimal('0.3'),
                status=status,
                score=85 + i*2 if status == 'COMPLETED' else None
            )
            exams_created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {exams_created} exam registrations'))

        # Mock Test Scores
        mock_tests = list(MockTest.objects.all())
        scores_created = 0
        for i, student in enumerate(students[:3]):
            for mock_test in mock_tests[:2]:
                MockTestScore.objects.create(
                    student=student, mock_test=mock_test,
                    score=70 + i*5, feedback=f'Good performance. Areas to improve: reading speed.'
                )
                scores_created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {scores_created} mock test scores'))

        # Additional payments
        for i, student in enumerate(students[4:7]):
            Payment.objects.create(
                student=student, amount=Decimal('5000'),
                payment_method='CASH',
                purpose='EXAM_FEE', status='COMPLETED',
                transaction_id=str(uuid.uuid4()).replace('-', '').upper()[:16]
            )

        self.stdout.write(self.style.SUCCESS('Done! Login credentials:'))
        self.stdout.write('  admin/admin123, student1-8/pass123, consultant1-3/pass123, trainer1-3/pass123')

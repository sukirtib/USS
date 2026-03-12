# CTLMS - Consultancy, Training & Learning Management System

A comprehensive Django-based system for educational consultancy organizations to manage student counseling, course training, batch management, and examination systems.

## Tech Stack

- **Backend:** Django 4.x (Python)
- **Database:** MySQL 8.0+
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5

## Quick Start

### 1. Create MySQL database

```sql
CREATE DATABASE ctlms_db;
```

### 2. Set database credentials (PowerShell)

```powershell
$env:DB_NAME = "ctlms_db"
$env:DB_USER = "root"
$env:DB_PASSWORD = "your_mysql_password"
```

Or create a `.env` file (copy from `.env.example`) and load it.

### 3. Create virtual environment (recommended)

```powershell
python -m venv venv
venv\Scripts\activate
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Run migrations

```powershell
python manage.py migrate
```

### 6. Create superuser (admin)

```powershell
python manage.py createsuperuser
```

### 7. (Optional) Load sample data

```powershell
python manage.py seed_data
```

Or manually in shell:

```powershell
python manage.py shell
```

Then in the shell:

```python
from core.models import User, Course, Batch, TrainerProfile, ConsultantProfile, StudentProfile
from django.contrib.auth.hashers import make_password

# Create admin
admin = User.objects.create_superuser('admin', 'admin@ctlms.com', 'admin123', first_name='Admin', last_name='User')
admin.role = 'ADMIN'
admin.save()

# Create sample course
course = Course.objects.create(course_code='IELTS', course_name='IELTS Preparation', duration_weeks=12, fee=25000)

# Create consultant & trainer (need User first)
consultant_user = User.objects.create_user('consultant1', 'c@test.com', 'pass123', first_name='Jane', last_name='Consultant', role='CONSULTANT')
ConsultantProfile.objects.create(user=consultant_user, specialization='Study Abroad')

trainer_user = User.objects.create_user('trainer1', 't@test.com', 'pass123', first_name='John', last_name='Trainer', role='TRAINER')
trainer = TrainerProfile.objects.create(user=trainer_user, subject_expertise='English', experience_years=5)

# Create batch
from datetime import date, time
Batch.objects.create(course=course, trainer=trainer, batch_name='IELTS Batch A', batch_code='IELTS-A1',
    start_date=date(2026, 3, 1), end_date=date(2026, 5, 31), start_time=time(9,0), end_time=time(11,0),
    capacity=20, status='UPCOMING')
```

### 8. Run server

```powershell
python manage.py runserver
```

Open http://127.0.0.1:8000

## Viewing the MySQL Database

- **MySQL Workbench:** Connect to localhost → open `ctlms_db` schema
- **Command line:** `mysql -u root -p` → `USE ctlms_db;` → `SHOW TABLES;`
- **Django dbshell:** `python manage.py dbshell` (opens MySQL client)

## User Roles

| Role | Access |
|------|--------|
| **Admin** | Full control, approve registrations/appointments, reports |
| **Student** | Book appointments, register for courses/exams, view progress |
| **Consultant** | View appointments, conduct counseling sessions |
| **Trainer** | View batches, enrolled students |

## Project Structure

```
Dbms/
├── ctlms/           # Django project settings
├── core/             # Main application
│   ├── models.py    # All entities
│   ├── views.py     # Role-based views
│   └── ...
├── templates/       # HTML templates
├── static/          # Static files
├── manage.py
└── requirements.txt
```

## Features

- ✅ User management (Admin, Student, Consultant, Trainer)
- ✅ Online counseling appointment booking
- ✅ Course registration
- ✅ Batch management
- ✅ Exam registration
- ✅ Enrollment processing
- ✅ Payment recording
- ✅ Reports (course enrollment, consultant sessions, financial)

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_studentprofile_trainer'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollment',
            name='batch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enrollments', to='core.batch'),
        ),
        migrations.AddField(
            model_name='examregistration',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_exams', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='examregistration',
            name='approved_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='MockTestScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.DecimalField(decimal_places=2, max_digits=5)),
                ('remarks', models.TextField(blank=True)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('mock_test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scores', to='core.mocktest')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mock_scores', to='core.studentprofile')),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recorded_scores', to='core.trainerprofile')),
            ],
            options={'ordering': ['-recorded_at'], 'unique_together': {('student', 'mock_test')}},
        ),
    ]

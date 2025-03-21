# Generated by Django 5.1.6 on 2025-03-16 18:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('appointments', '0002_initial'),
        ('core', '0001_initial'),
        ('professionals', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='professional',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='professionals.professional'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='rescheduled_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='rescheduled_from', to='appointments.appointment'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='service',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='core.service'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='shift',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments', to='professionals.shift'),
        ),
        migrations.AlterUniqueTogether(
            name='appointment',
            unique_together={('professional', 'patient', 'scheduled_to')},
        ),
    ]

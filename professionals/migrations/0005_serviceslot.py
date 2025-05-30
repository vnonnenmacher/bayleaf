# Generated by Django 5.1.7 on 2025-05-28 23:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('professionals', '0004_professional_avatar'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='professionals.shift')),
            ],
            options={
                'verbose_name': 'Service Slot',
                'verbose_name_plural': 'Service Slots',
                'unique_together': {('shift', 'start_time')},
            },
        ),
    ]

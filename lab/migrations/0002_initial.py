# Generated by Django 5.1.6 on 2025-03-24 00:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lab', '0001_initial'),
        ('patients', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='sample',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='samples', to='patients.patient'),
        ),
        migrations.AddField(
            model_name='allowedstatetransition',
            name='from_state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='allowed_transitions', to='lab.samplestate'),
        ),
        migrations.AddField(
            model_name='allowedstatetransition',
            name='to_state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_transitions', to='lab.samplestate'),
        ),
        migrations.AddField(
            model_name='samplestatetransition',
            name='changed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='samplestatetransition',
            name='new_state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='new_transitions', to='lab.samplestate'),
        ),
        migrations.AddField(
            model_name='samplestatetransition',
            name='previous_state',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='previous_transitions', to='lab.samplestate'),
        ),
        migrations.AddField(
            model_name='samplestatetransition',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='state_transitions', to='lab.sample'),
        ),
        migrations.AddField(
            model_name='sample',
            name='sample_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='samples', to='lab.sampletype'),
        ),
    ]

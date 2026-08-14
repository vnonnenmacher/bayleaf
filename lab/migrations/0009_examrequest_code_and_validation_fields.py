from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("lab", "0008_sector"),
    ]

    operations = [
        migrations.AddField(
            model_name="examrequest",
            name="code",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="examrequest",
            name="is_validated",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="examrequest",
            name="validated_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="validated_exam_requests", to="professionals.professional"),
        ),
    ]

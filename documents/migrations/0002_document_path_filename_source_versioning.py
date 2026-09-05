import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="document",
            name="content_hash",
        ),
        migrations.AddField(
            model_name="document",
            name="md5sum",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="document",
            name="path",
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name="document",
            name="file_name",
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name="document",
            name="source",
            field=models.CharField(
                choices=[("minio", "MinIO"), ("ad", "Active Directory"), ("other", "Other")],
                default="minio",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="document",
            name="version",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="document",
            name="parent_document",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="versions",
                to="documents.document",
            ),
        ),
        migrations.AlterField(
            model_name="document",
            name="doc_key",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AlterField(
            model_name="document",
            name="reference",
            field=models.CharField(blank=True, max_length=1024),
        ),
        migrations.AlterField(
            model_name="document",
            name="mime_type",
            field=models.CharField(blank=True, max_length=128),
        ),
    ]

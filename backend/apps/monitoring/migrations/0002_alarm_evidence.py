from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("monitoring", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="alarm",
            name="evidence_status",
            field=models.CharField(
                choices=[
                    ("NONE", "None"),
                    ("PENDING", "Pending"),
                    ("READY", "Ready"),
                    ("FAILED", "Failed"),
                ],
                default="NONE",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="alarm",
            name="snapshot_object",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="alarm",
            name="clip_object",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="alarm",
            name="evidence_error",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]

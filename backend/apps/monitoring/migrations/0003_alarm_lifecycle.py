from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("monitoring", "0002_alarm_evidence"),
    ]

    operations = [
        migrations.AddField(
            model_name="alarm",
            name="condition_key",
            field=models.CharField(blank=True, db_index=True, max_length=32),
        ),
        migrations.AddField(
            model_name="alarm",
            name="active",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="alarm",
            name="resolved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

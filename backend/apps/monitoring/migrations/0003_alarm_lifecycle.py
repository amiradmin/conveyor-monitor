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
        migrations.AddConstraint(
            model_name="alarm",
            constraint=models.UniqueConstraint(
                fields=("conveyor", "condition_key"),
                condition=models.Q(active=True) & ~models.Q(condition_key=""),
                name="uniq_active_alarm_condition",
            ),
        ),
    ]

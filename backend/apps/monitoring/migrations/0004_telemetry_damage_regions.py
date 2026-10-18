from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0003_alarm_lifecycle")]
    operations = [
        migrations.AddField(model_name="telemetrysample", name="damage_regions", field=models.JSONField(default=list, blank=True)),
        migrations.AddField(model_name="telemetrysample", name="source_position_seconds", field=models.FloatField(null=True, blank=True)),
    ]

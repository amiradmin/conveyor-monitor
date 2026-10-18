from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0003_alarm_lifecycle")]
    operations = [migrations.AddField(model_name="telemetrysample", name="vision_details", field=models.JSONField(default=dict, blank=True))]

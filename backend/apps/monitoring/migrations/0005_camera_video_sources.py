from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("monitoring", "0004_telemetry_damage_regions")]
    operations = [
        migrations.AddField(model_name="camera", name="video_source", field=models.CharField(max_length=150, blank=True)),
        migrations.AddField(model_name="camera", name="video_file", field=models.FileField(upload_to="videos/", blank=True)),
        migrations.AddField(model_name="camera", name="source_changed_at", field=models.DateTimeField(null=True, blank=True)),
    ]

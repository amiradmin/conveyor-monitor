from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Conveyor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=50, unique=True)),
                ("name", models.CharField(max_length=150)),
                ("belt_width_mm", models.PositiveIntegerField(default=1200)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Camera",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("role", models.CharField(choices=[("TOP", "Top view"), ("SIDE", "Side view"), ("VERIFY", "Verification")], max_length=16)),
                ("rtsp_url", models.CharField(blank=True, max_length=500)),
                ("active", models.BooleanField(default=True)),
                ("conveyor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cameras", to="monitoring.conveyor")),
            ],
        ),
        migrations.CreateModel(
            name="TelemetrySample",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ts", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("speed_mps", models.FloatField(blank=True, null=True)),
                ("alignment_offset_mm", models.FloatField(blank=True, null=True)),
                ("volume_m3h", models.FloatField(blank=True, null=True)),
                ("tear_probability", models.FloatField(blank=True, null=True)),
                ("confidence", models.FloatField(blank=True, null=True)),
                ("conveyor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="samples", to="monitoring.conveyor")),
            ],
        ),
        migrations.CreateModel(
            name="Alarm",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=100)),
                ("severity", models.CharField(choices=[("INFO", "Info"), ("WARNING", "Warning"), ("CRITICAL", "Critical")], max_length=16)),
                ("message", models.CharField(max_length=500)),
                ("acknowledged", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("conveyor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="alarms", to="monitoring.conveyor")),
            ],
        ),
    ]

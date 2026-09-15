from django.db import models


class Conveyor(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    belt_width_mm = models.PositiveIntegerField(default=1200)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.code


class Camera(models.Model):
    class Role(models.TextChoices):
        TOP = "TOP", "Top view"
        SIDE = "SIDE", "Side view"
        VERIFY = "VERIFY", "Verification"

    conveyor = models.ForeignKey(Conveyor, on_delete=models.CASCADE, related_name="cameras")
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=16, choices=Role.choices)
    rtsp_url = models.CharField(max_length=500, blank=True)
    active = models.BooleanField(default=True)


class TelemetrySample(models.Model):
    conveyor = models.ForeignKey(Conveyor, on_delete=models.CASCADE, related_name="samples")
    ts = models.DateTimeField(auto_now_add=True, db_index=True)
    speed_mps = models.FloatField(null=True, blank=True)
    alignment_offset_mm = models.FloatField(null=True, blank=True)
    volume_m3h = models.FloatField(null=True, blank=True)
    tear_probability = models.FloatField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)


class Alarm(models.Model):
    class Severity(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"

    conveyor = models.ForeignKey(Conveyor, on_delete=models.CASCADE, related_name="alarms")
    code = models.CharField(max_length=100)
    severity = models.CharField(max_length=16, choices=Severity.choices)
    message = models.CharField(max_length=500)
    acknowledged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

from rest_framework import serializers
from .models import Alarm, Camera, Conveyor, TelemetrySample


class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = "__all__"


class ConveyorSerializer(serializers.ModelSerializer):
    cameras = CameraSerializer(many=True, read_only=True)

    class Meta:
        model = Conveyor
        fields = "__all__"


class TelemetrySampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemetrySample
        fields = "__all__"


class AlarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alarm
        fields = "__all__"


class ConveyorWriteSerializer(serializers.Serializer):
    code = serializers.RegexField(r"^[A-Z0-9][A-Z0-9_-]{0,49}$", max_length=50, required=False)
    name = serializers.CharField(max_length=150, required=False)
    belt_width_mm = serializers.IntegerField(min_value=100, max_value=10000, required=False)
    active = serializers.BooleanField(required=False)
    camera_name = serializers.CharField(max_length=100, required=False)
    video_source = serializers.ChoiceField(choices=["conveyor_1.mp4", "conveyor_1_old.mp4"], required=False)
    video_file = serializers.FileField(required=False)

    def validate_video_file(self, value):
        from pathlib import Path
        from uuid import uuid4
        extension = Path(value.name).suffix.lower()
        if extension not in {".mp4", ".webm"} or value.size > 500 * 1024 * 1024:
            raise serializers.ValidationError("Upload an MP4 or WebM video smaller than 500 MB.")
        header = value.read(32)
        value.seek(0)
        if not (extension == ".mp4" and b"ftyp" in header) and not (extension == ".webm" and header.startswith(b"\x1a\x45\xdf\xa3")):
            raise serializers.ValidationError("The file is not a supported video.")
        value.name = f"{uuid4().hex}{extension}"
        return value

    def validate(self, values):
        if values.get("video_file") and values.get("video_source"):
            raise serializers.ValidationError("Choose one video source.")
        if not self.partial:
            for key in ("code", "name"):
                if not values.get(key):
                    raise serializers.ValidationError({key: "This field is required."})
            if not values.get("video_file") and not values.get("video_source"):
                raise serializers.ValidationError("Choose a video source.")
        return values

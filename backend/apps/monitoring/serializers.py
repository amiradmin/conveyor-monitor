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

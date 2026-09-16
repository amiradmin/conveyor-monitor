import requests
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Conveyor
from .serializers import ConveyorSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "service": "backend", "time": timezone.now()})


@api_view(["GET"])
def conveyors(request):
    items = Conveyor.objects.prefetch_related("cameras").all().order_by("code")
    return Response(ConveyorSerializer(items, many=True).data)


@api_view(["GET"])
def demo_status(request):
    return Response(
        {
            "conveyor": "CV-01",
            "state": "RUNNING",
            "speed_mps": 2.43,
            "alignment_offset_mm": 12.0,
            "alignment_status": "NORMAL",
            "volume_m3h": 312.0,
            "mass_flow_tph": 412.0,
            "nominal_capacity_tph": 600.0,
            "tear_probability": 0.01,
            "tear_status": "NORMAL",
            "ai_confidence": 0.96,
            "plc_write_enabled": False,
            "plc_state": "AUTO_RUNNING",
        }
    )


@api_view(["POST"])
def controlled_stop(request):
    payload = {
        "conveyor_id": request.data.get("conveyor_id", "CV-01"),
        "reason": request.data.get("reason", "operator request"),
        "armed": bool(request.data.get("armed", False)),
    }
    try:
        response = requests.post(f"{settings.PLC_GATEWAY_URL}/stop-request", json=payload, timeout=3)
        return Response(response.json(), status=response.status_code)
    except requests.RequestException as exc:
        return Response({"status": "error", "detail": str(exc)}, status=503)

from __future__ import annotations

import threading
from datetime import timedelta
from typing import Any

import requests
from django.conf import settings
from django.db import close_old_connections
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Alarm, Conveyor, TelemetrySample
from .serializers import AlarmSerializer, ConveyorSerializer, TelemetrySampleSerializer


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mass_flow_tph(volume_m3h: float) -> float:
    return max(0.0, volume_m3h * settings.BULK_DENSITY_T_PER_M3)


def _load_percent(volume_m3h: float) -> float:
    capacity = max(settings.NOMINAL_CAPACITY_TPH, 0.001)
    return (_mass_flow_tph(volume_m3h) / capacity) * 100.0


def _alignment_status(offset_mm: float) -> str:
    absolute = abs(offset_mm)
    if absolute >= settings.ALIGNMENT_CRITICAL_MM:
        return "CRITICAL"
    if absolute >= settings.ALIGNMENT_WARNING_MM:
        return "WARNING"
    return "NORMAL"


def _tear_status(probability: float) -> str:
    if probability >= settings.TEAR_CRITICAL_PROBABILITY:
        return "CRITICAL"
    if probability >= settings.TEAR_WARNING_PROBABILITY:
        return "WARNING"
    return "NORMAL"


def _capture_alarm_evidence(alarm_id: int) -> None:
    """Capture evidence without blocking telemetry ingestion.

    This lightweight background thread is sufficient for the current single-site
    deployment. A production multi-site deployment can replace it with Celery or
    another durable task queue without changing the API contract.
    """
    if not settings.EVIDENCE_CAPTURE_ENABLED:
        return

    close_old_connections()
    try:
        alarm = Alarm.objects.select_related("conveyor").get(pk=alarm_id)
        payload = {
            "alarm_id": alarm.id,
            "conveyor_id": alarm.conveyor.code,
            "code": alarm.code,
            "severity": alarm.severity,
            "message": alarm.message,
            "created_at": alarm.created_at.isoformat(),
        }
        try:
            response = requests.post(
                f"{settings.VISION_SERVICE_URL}/evidence",
                json=payload,
                timeout=settings.EVIDENCE_CAPTURE_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            evidence = response.json()
            alarm.snapshot_object = str(evidence.get("snapshot_object", ""))
            alarm.clip_object = str(evidence.get("clip_object", ""))
            alarm.evidence_status = (
                Alarm.EvidenceStatus.READY
                if alarm.snapshot_object or alarm.clip_object
                else Alarm.EvidenceStatus.FAILED
            )
            alarm.evidence_error = (
                ""
                if alarm.evidence_status == Alarm.EvidenceStatus.READY
                else "No evidence objects returned."
            )
        except (requests.RequestException, ValueError, TypeError) as exc:
            alarm.evidence_status = Alarm.EvidenceStatus.FAILED
            alarm.evidence_error = str(exc)[:500]

        alarm.save(
            update_fields=[
                "snapshot_object",
                "clip_object",
                "evidence_status",
                "evidence_error",
            ]
        )
    except Alarm.DoesNotExist:
        return
    finally:
        close_old_connections()


def _queue_alarm_evidence(alarm: Alarm) -> None:
    if not settings.EVIDENCE_CAPTURE_ENABLED:
        return
    threading.Thread(
        target=_capture_alarm_evidence,
        args=(alarm.id,),
        name=f"alarm-evidence-{alarm.id}",
        daemon=True,
    ).start()


def _emit_alarm(conveyor: Conveyor, code: str, severity: str, message: str) -> Alarm | None:
    cutoff = timezone.now() - timedelta(seconds=settings.ALARM_COOLDOWN_SECONDS)
    exists = Alarm.objects.filter(
        conveyor=conveyor,
        code=code,
        acknowledged=False,
        created_at__gte=cutoff,
    ).exists()
    if exists:
        return None

    alarm = Alarm.objects.create(
        conveyor=conveyor,
        code=code,
        severity=severity,
        message=message,
        evidence_status=(
            Alarm.EvidenceStatus.PENDING
            if settings.EVIDENCE_CAPTURE_ENABLED
            else Alarm.EvidenceStatus.NONE
        ),
    )
    _queue_alarm_evidence(alarm)
    return alarm


def _evaluate_alarms(conveyor: Conveyor, sample: TelemetrySample) -> None:
    alignment = _float(sample.alignment_offset_mm)
    tear_probability = _float(sample.tear_probability)
    load_percent = _load_percent(_float(sample.volume_m3h))

    if abs(alignment) >= settings.ALIGNMENT_CRITICAL_MM:
        _emit_alarm(
            conveyor,
            "ALIGNMENT_CRITICAL",
            Alarm.Severity.CRITICAL,
            f"Belt alignment offset is {alignment:.1f} mm.",
        )
    elif abs(alignment) >= settings.ALIGNMENT_WARNING_MM:
        _emit_alarm(
            conveyor,
            "ALIGNMENT_WARNING",
            Alarm.Severity.WARNING,
            f"Belt alignment offset is {alignment:.1f} mm.",
        )

    if tear_probability >= settings.TEAR_CRITICAL_PROBABILITY:
        _emit_alarm(
            conveyor,
            "TEAR_CRITICAL",
            Alarm.Severity.CRITICAL,
            f"Tear probability reached {tear_probability:.0%}.",
        )
    elif tear_probability >= settings.TEAR_WARNING_PROBABILITY:
        _emit_alarm(
            conveyor,
            "TEAR_WARNING",
            Alarm.Severity.WARNING,
            f"Tear probability reached {tear_probability:.0%}.",
        )

    if load_percent >= settings.OVERLOAD_CRITICAL_PERCENT:
        _emit_alarm(
            conveyor,
            "OVERLOAD_CRITICAL",
            Alarm.Severity.CRITICAL,
            f"Conveyor load reached {load_percent:.0f}% of nominal capacity.",
        )
    elif load_percent >= settings.OVERLOAD_WARNING_PERCENT:
        _emit_alarm(
            conveyor,
            "OVERLOAD_WARNING",
            Alarm.Severity.WARNING,
            f"Conveyor load reached {load_percent:.0f}% of nominal capacity.",
        )


def _create_sample(conveyor: Conveyor, payload: dict[str, Any]) -> TelemetrySample:
    sample = TelemetrySample.objects.create(
        conveyor=conveyor,
        speed_mps=_float(payload.get("speed_mps", payload.get("belt_speed_mps"))),
        alignment_offset_mm=_float(payload.get("alignment_offset_mm")),
        volume_m3h=_float(payload.get("volume_m3h")),
        tear_probability=max(0.0, min(1.0, _float(payload.get("tear_probability")))),
        confidence=max(0.0, min(1.0, _float(payload.get("ai_confidence", payload.get("confidence"))))),
    )
    _evaluate_alarms(conveyor, sample)
    return sample


def _latest_sample(conveyor: Conveyor) -> TelemetrySample | None:
    return conveyor.samples.order_by("-ts").first()


def _refresh_from_vision(conveyor: Conveyor) -> TelemetrySample | None:
    try:
        response = requests.get(f"{settings.VISION_SERVICE_URL}/demo", timeout=2.5)
        response.raise_for_status()
        payload = response.json()
        return _create_sample(conveyor, payload)
    except (requests.RequestException, ValueError, TypeError):
        return None


def _get_fresh_sample(conveyor: Conveyor) -> tuple[TelemetrySample | None, str]:
    latest = _latest_sample(conveyor)
    stale_after = timedelta(seconds=settings.TELEMETRY_STALE_SECONDS)
    if latest and timezone.now() - latest.ts <= stale_after:
        return latest, "database"

    refreshed = _refresh_from_vision(conveyor)
    if refreshed:
        return refreshed, "vision-service"
    if latest:
        return latest, "stale-database"
    return None, "unavailable"


def _status_payload(conveyor: Conveyor, sample: TelemetrySample, source: str) -> dict[str, Any]:
    speed = _float(sample.speed_mps)
    alignment = _float(sample.alignment_offset_mm)
    volume = _float(sample.volume_m3h)
    tear_probability = _float(sample.tear_probability)
    confidence = _float(sample.confidence)
    mass_flow = _mass_flow_tph(volume)
    load_percent = _load_percent(volume)

    state = "RUNNING" if speed > 0.05 else "STOPPED"
    if source == "stale-database":
        state = "STALE"

    return {
        "conveyor": conveyor.code,
        "state": state,
        "telemetry_source": source,
        "telemetry_ts": sample.ts,
        "speed_mps": speed,
        "alignment_offset_mm": alignment,
        "alignment_status": _alignment_status(alignment),
        "volume_m3h": volume,
        "mass_flow_tph": round(mass_flow, 2),
        "material_flow_tph": round(mass_flow, 2),
        "nominal_capacity_tph": settings.NOMINAL_CAPACITY_TPH,
        "load_percent": round(load_percent, 1),
        "tear_probability": tear_probability,
        "tear_status": _tear_status(tear_probability),
        "ai_confidence": confidence,
        "plc_write_enabled": settings.PLC_WRITE_ENABLED,
        "plc_state": "AUTO_RUNNING" if state == "RUNNING" else state,
    }


def _status_response(code: str) -> Response:
    conveyor, _ = Conveyor.objects.get_or_create(code=code, defaults={"name": f"Conveyor {code}"})
    sample, source = _get_fresh_sample(conveyor)
    if not sample:
        return Response(
            {
                "status": "error",
                "detail": "No telemetry is available from the database or vision service.",
                "conveyor": code,
            },
            status=http_status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response(_status_payload(conveyor, sample, source))


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "service": "backend", "time": timezone.now()})


@api_view(["GET"])
def conveyors(request):
    items = Conveyor.objects.prefetch_related("cameras").all().order_by("code")
    return Response(ConveyorSerializer(items, many=True).data)


@api_view(["GET"])
def conveyor_status(request, code: str = "CV-01"):
    return _status_response(code)


@api_view(["GET"])
def demo_status(request):
    return _status_response("CV-01")


@api_view(["POST"])
@permission_classes([AllowAny])
def ingest_telemetry(request):
    token = request.headers.get("X-Internal-Token", "")
    if token != settings.INTERNAL_SERVICE_TOKEN:
        return Response({"detail": "Invalid internal service token."}, status=http_status.HTTP_403_FORBIDDEN)

    code = str(request.data.get("conveyor", request.data.get("conveyor_id", "CV-01"))).strip() or "CV-01"
    conveyor, _ = Conveyor.objects.get_or_create(code=code, defaults={"name": f"Conveyor {code}"})
    sample = _create_sample(conveyor, dict(request.data))
    return Response(TelemetrySampleSerializer(sample).data, status=http_status.HTTP_201_CREATED)


@api_view(["GET"])
def events(request):
    code = request.query_params.get("conveyor", "CV-01")
    try:
        requested_limit = int(request.query_params.get("limit", "20"))
    except (TypeError, ValueError):
        requested_limit = 20
    limit = min(max(requested_limit, 1), 100)

    queryset = Alarm.objects.select_related("conveyor").filter(conveyor__code=code).order_by("-created_at")
    acknowledged = request.query_params.get("acknowledged")
    if acknowledged in {"true", "false"}:
        queryset = queryset.filter(acknowledged=acknowledged == "true")

    return Response(AlarmSerializer(queryset[:limit], many=True).data)


@api_view(["POST"])
def acknowledge_alarm(request, alarm_id: int):
    alarm = get_object_or_404(Alarm, pk=alarm_id)
    alarm.acknowledged = True
    alarm.save(update_fields=["acknowledged"])
    return Response(AlarmSerializer(alarm).data)


@api_view(["POST"])
def recapture_alarm_evidence(request, alarm_id: int):
    alarm = get_object_or_404(Alarm, pk=alarm_id)
    if not settings.EVIDENCE_CAPTURE_ENABLED:
        return Response(
            {"detail": "Evidence capture is disabled."},
            status=http_status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    alarm.evidence_status = Alarm.EvidenceStatus.PENDING
    alarm.evidence_error = ""
    alarm.save(update_fields=["evidence_status", "evidence_error"])
    _queue_alarm_evidence(alarm)
    return Response(AlarmSerializer(alarm).data, status=http_status.HTTP_202_ACCEPTED)


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
        return Response({"status": "error", "detail": str(exc)}, status=http_status.HTTP_503_SERVICE_UNAVAILABLE)

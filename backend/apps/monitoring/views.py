from __future__ import annotations

import threading
from datetime import timedelta
from typing import Any
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.db import IntegrityError, close_old_connections, transaction
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from minio import Minio
from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Alarm, Camera, Conveyor, TelemetrySample
from .serializers import AlarmSerializer, ConveyorSerializer, ConveyorWriteSerializer, TelemetrySampleSerializer


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


def _minio_client(endpoint_value: str, *, secure: bool) -> Minio:
    raw = endpoint_value.strip()
    endpoint = raw
    resolved_secure = secure
    if "://" in raw:
        parsed = urlparse(raw)
        endpoint = parsed.netloc
        resolved_secure = parsed.scheme == "https"
    return Minio(
        endpoint,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=resolved_secure,
        region=settings.MINIO_REGION,
    )


def _capture_alarm_evidence(alarm_id: int) -> None:
    """Capture evidence without blocking telemetry ingestion."""
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


def _create_active_alarm(
    conveyor: Conveyor,
    condition_key: str,
    code: str,
    severity: str,
    message: str,
) -> Alarm:
    try:
        alarm = Alarm.objects.create(
            conveyor=conveyor,
            condition_key=condition_key,
            code=code,
            severity=severity,
            message=message,
            active=True,
            evidence_status=(
                Alarm.EvidenceStatus.PENDING
                if settings.EVIDENCE_CAPTURE_ENABLED
                else Alarm.EvidenceStatus.NONE
            ),
        )
    except IntegrityError:
        existing = Alarm.objects.filter(
            conveyor=conveyor,
            condition_key=condition_key,
            active=True,
        ).order_by("-created_at").first()
        if existing is not None:
            return existing
        raise

    _queue_alarm_evidence(alarm)
    return alarm


def _resolve_alarm(alarm: Alarm) -> None:
    if not alarm.active:
        return
    alarm.active = False
    alarm.resolved_at = timezone.now()
    alarm.save(update_fields=["active", "resolved_at"])


def _sync_alarm_condition(
    conveyor: Conveyor,
    *,
    condition_key: str,
    value: float,
    warning_threshold: float,
    critical_threshold: float,
    recovery_threshold: float,
    warning_code: str,
    critical_code: str,
    message: str,
) -> None:
    """Latch one alarm per condition until a lower recovery threshold is crossed.

    Acknowledgement is intentionally independent of condition state. ACK silences
    the operator-facing notification, but the alarm remains active and cannot be
    re-created while the measured condition persists. Warning alarms may escalate
    to critical; critical alarms remain latched until full recovery.
    """
    active_alarm = (
        Alarm.objects.filter(
            conveyor=conveyor,
            condition_key=condition_key,
            active=True,
        )
        .order_by("-created_at")
        .first()
    )

    if active_alarm is not None:
        if value < recovery_threshold:
            _resolve_alarm(active_alarm)
            return

        if active_alarm.severity == Alarm.Severity.CRITICAL:
            return

        if value >= critical_threshold:
            _resolve_alarm(active_alarm)
            _create_active_alarm(
                conveyor,
                condition_key,
                critical_code,
                Alarm.Severity.CRITICAL,
                message,
            )
        return

    if value >= critical_threshold:
        _create_active_alarm(
            conveyor,
            condition_key,
            critical_code,
            Alarm.Severity.CRITICAL,
            message,
        )
    elif value >= warning_threshold:
        _create_active_alarm(
            conveyor,
            condition_key,
            warning_code,
            Alarm.Severity.WARNING,
            message,
        )


def _evaluate_alarms(conveyor: Conveyor, sample: TelemetrySample) -> None:
    alignment = _float(sample.alignment_offset_mm)
    alignment_magnitude = abs(alignment)
    tear_probability = _float(sample.tear_probability)
    load_percent = _load_percent(_float(sample.volume_m3h))

    _sync_alarm_condition(
        conveyor,
        condition_key="ALIGNMENT",
        value=alignment_magnitude,
        warning_threshold=settings.ALIGNMENT_WARNING_MM,
        critical_threshold=settings.ALIGNMENT_CRITICAL_MM,
        recovery_threshold=settings.ALIGNMENT_RECOVERY_MM,
        warning_code="ALIGNMENT_WARNING",
        critical_code="ALIGNMENT_CRITICAL",
        message=f"Belt alignment offset is {alignment:.1f} mm.",
    )
    _sync_alarm_condition(
        conveyor,
        condition_key="TEAR",
        value=max(tear_probability, settings.TEAR_CRITICAL_PROBABILITY) if sample.damage_regions else tear_probability,
        warning_threshold=settings.TEAR_WARNING_PROBABILITY,
        critical_threshold=settings.TEAR_CRITICAL_PROBABILITY,
        recovery_threshold=settings.TEAR_RECOVERY_PROBABILITY,
        warning_code="BELT_ANOMALY_WARNING" if conveyor.code == "CV-02" else "TEAR_WARNING",
        critical_code="BELT_ANOMALY_CRITICAL" if conveyor.code == "CV-02" else "TEAR_CRITICAL",
        message=(f"Visible belt-edge anomaly score reached {tear_probability:.0%}." if conveyor.code == "CV-02" else "Belt edge tear detected. Immediate inspection required." if sample.damage_regions else f"Tear probability reached {tear_probability:.0%}."),
    )
    _sync_alarm_condition(
        conveyor,
        condition_key="OVERLOAD",
        value=load_percent,
        warning_threshold=settings.OVERLOAD_WARNING_PERCENT,
        critical_threshold=settings.OVERLOAD_CRITICAL_PERCENT,
        recovery_threshold=settings.OVERLOAD_RECOVERY_PERCENT,
        warning_code="OVERLOAD_WARNING",
        critical_code="OVERLOAD_CRITICAL",
        message=f"Conveyor load reached {load_percent:.0f}% of nominal capacity.",
    )


def _create_sample(conveyor: Conveyor, payload: dict[str, Any]) -> TelemetrySample:
    sample = TelemetrySample.objects.create(
        conveyor=conveyor,
        vision_details={
            "anomaly_score": payload.get("anomaly_score", 0.0),
            "anomaly_regions": payload.get("anomaly_regions", []),
            "detector_warming_up": payload.get("detector_warming_up", False),
        },
        damage_regions=payload.get("damage_regions", []),
        source_position_seconds=payload.get("source_position_seconds"),
        speed_mps=_float(payload.get("speed_mps", payload.get("belt_speed_mps"))),
        alignment_offset_mm=_float(payload.get("alignment_offset_mm")),
        volume_m3h=_float(payload.get("volume_m3h")),
        tear_probability=max(0.0, min(1.0, _float(payload.get("tear_probability")))),
        confidence=max(0.0, min(1.0, _float(payload.get("ai_confidence", payload.get("confidence"))))),
    )
    _evaluate_alarms(conveyor, sample)
    return sample


def _latest_sample(conveyor: Conveyor) -> TelemetrySample | None:
    samples = conveyor.samples.all()
    camera = conveyor.cameras.filter(role="TOP").order_by("id").first()
    if camera and camera.source_changed_at:
        samples = samples.filter(ts__gte=camera.source_changed_at)
    return samples.order_by("-ts").first()


def _source_matches(conveyor, payload):
    if not conveyor.active:
        return False
    camera = conveyor.cameras.filter(role="TOP").order_by("id").first()
    if camera and not camera.active:
        return False
    if camera and camera.source_changed_at:
        return payload.get("source_revision") == camera.source_changed_at.isoformat()
    return True


def _refresh_from_vision(conveyor: Conveyor) -> TelemetrySample | None:
    try:
        response = requests.get(
            f"{settings.VISION_SERVICE_URL}/conveyors/{conveyor.code}/live",
            params={"conveyor_id": conveyor.code},
            timeout=2.5,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("conveyor_id") != conveyor.code or not _source_matches(conveyor, payload):
            return None
        return _create_sample(conveyor, payload)
    except (requests.RequestException, ValueError, TypeError):
        return None


def _get_fresh_sample(conveyor: Conveyor) -> tuple[TelemetrySample | None, str]:
    latest = _latest_sample(conveyor)
    stale_after = timedelta(seconds=settings.TELEMETRY_STALE_SECONDS)
    if latest and timezone.now() - latest.ts <= stale_after:
        return latest, "database"

    refreshed = _refresh_from_vision(conveyor) if conveyor.active else None
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
        "damage_regions": sample.damage_regions,
        "vision_details": sample.vision_details,
        "source_position_seconds": sample.source_position_seconds,
        "tear_probability": tear_probability,
        "tear_status": "CRITICAL" if sample.damage_regions else _tear_status(tear_probability),
        "ai_confidence": confidence,
        "active_alarm_count": conveyor.alarms.filter(active=True).count(),
        "plc_write_enabled": settings.PLC_WRITE_ENABLED,
        "plc_state": "AUTO_RUNNING" if state == "RUNNING" else state,
    }


def _status_response(code: str) -> Response:
    conveyor = get_object_or_404(Conveyor, code=code)
    if not conveyor.active:
        return Response({"conveyor": code, "state": "DISABLED"})
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


def _conveyor_item(conveyor):
    camera = conveyor.cameras.filter(role="TOP").order_by("id").first()
    source = (camera.video_source if camera else "") or ("conveyor_1.mp4" if conveyor.code == "CV-01" and not (camera and camera.video_file) else "")
    item = {"id": conveyor.id, "code": conveyor.code, "name": conveyor.name,
            "active": conveyor.active, "belt_width_mm": conveyor.belt_width_mm,
            "camera_name": camera.name if camera else conveyor.code,
            "video_source": source, "video_name": camera.video_file.name.rsplit("/", 1)[-1] if camera and camera.video_file else source,
            "video_endpoint": f"/conveyors/{conveyor.code}/video/" if camera and camera.video_file else None}
    sample = _latest_sample(conveyor)
    fresh = sample and timezone.now() - sample.ts <= timedelta(seconds=settings.TELEMETRY_STALE_SECONDS)
    item["status"] = _status_payload(conveyor, sample, "database" if fresh else "stale-database") if sample else None
    item["state"] = "DISABLED" if not conveyor.active else (item["status"]["state"] if sample else "UNAVAILABLE")
    pending = conveyor.alarms.filter(active=True, acknowledged=False)
    item["pending_alarm_count"] = pending.count()
    item["critical_alarm_count"] = pending.filter(severity="CRITICAL").count()
    return item


def _save_conveyor(request, conveyor=None):
    serializer = ConveyorWriteSerializer(data=request.data, partial=conveyor is not None)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    if conveyor and "code" in values and values["code"] != conveyor.code:
        return Response({"detail": "The conveyor identifier cannot be changed."}, status=400)
    if not conveyor and Conveyor.objects.filter(code=values["code"]).exists():
        return Response({"code": ["This identifier is already registered."]}, status=400)
    width_changed = conveyor and "belt_width_mm" in values and values["belt_width_mm"] != conveyor.belt_width_mm
    with transaction.atomic():
        if not conveyor:
            conveyor = Conveyor.objects.create(**{key: values[key] for key in ("code", "name", "belt_width_mm", "active") if key in values})
        else:
            for key in ("name", "belt_width_mm", "active"):
                if key in values:
                    setattr(conveyor, key, values[key])
            conveyor.save()
        camera, _ = Camera.objects.get_or_create(conveyor=conveyor, role="TOP", defaults={"name": values.get("camera_name", conveyor.code)})
        if "camera_name" in values:
            camera.name = values["camera_name"]
        if "video_file" in values or "video_source" in values:
            camera.video_file = values.get("video_file", "")
            camera.video_source = values.get("video_source", "")
            camera.source_changed_at = timezone.now()
        if width_changed:
            camera.source_changed_at = timezone.now()
        camera.save()
    return Response(_conveyor_item(conveyor), status=200 if request.method == "PATCH" else 201)


@api_view(["GET", "POST"])
def conveyors(request):
    if request.method == "POST":
        return _save_conveyor(request)
    items = Conveyor.objects.prefetch_related("cameras").order_by("code")
    return Response([_conveyor_item(item) for item in items])


@api_view(["PATCH"])
def update_conveyor(request, code):
    return _save_conveyor(request, get_object_or_404(Conveyor, code=code))


@api_view(["GET"])
def conveyor_video(request, code):
    camera = get_object_or_404(Camera, conveyor__code=code, role="TOP")
    if not camera.video_file:
        return Response({"detail": "No uploaded video."}, status=404)
    return FileResponse(camera.video_file.open("rb"), content_type="video/webm" if camera.video_file.name.endswith(".webm") else "video/mp4")


@api_view(["GET"])
@permission_classes([AllowAny])
def vision_sources(request):
    if request.headers.get("X-Internal-Token") != settings.INTERNAL_SERVICE_TOKEN:
        return Response({"detail": "Invalid internal service token."}, status=403)
    sources = []
    for conveyor in Conveyor.objects.filter(active=True).prefetch_related("cameras"):
        camera = conveyor.cameras.filter(role="TOP").order_by("id").first()
        if camera and not camera.active:
            continue
        source = ""
        if camera and camera.video_file:
            source = f"/uploads/{camera.video_file.name}"
        elif camera and camera.video_source:
            source = f"/data/{camera.video_source}"
        elif conveyor.code == "CV-01" and not (camera and camera.rtsp_url):
            source = "/data/conveyor_1.mp4"
        if source:
            sources.append({"conveyor_id": conveyor.code, "source": source, "belt_width_mm": conveyor.belt_width_mm,
                            "revision": camera.source_changed_at.isoformat() if camera and camera.source_changed_at else "legacy"})
    return Response(sources)


@api_view(["GET"])
def conveyor_status(request, code: str = "CV-01"):
    return _status_response(code)


@api_view(["GET"])
def conveyor_frame(request, code: str):
    if code not in {"CV-01", "CV-02"}:
        return Response({"detail": "Unknown conveyor"}, status=http_status.HTTP_404_NOT_FOUND)
    try:
        response = requests.get(
            f"{settings.VISION_SERVICE_URL}/frame.jpg",
            params={"conveyor_id": code},
            timeout=2.5,
        )
        response.raise_for_status()
        return HttpResponse(response.content, content_type="image/jpeg", headers={"Cache-Control": "no-store"})
    except requests.RequestException:
        return Response({"detail": "Camera frame unavailable"}, status=http_status.HTTP_503_SERVICE_UNAVAILABLE)


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
    if not _source_matches(conveyor, request.data):
        return Response({"detail": "This video source is no longer enabled or current."}, status=409)
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
    active = request.query_params.get("active")
    if active in {"true", "false"}:
        queryset = queryset.filter(active=active == "true")

    return Response(AlarmSerializer(queryset[:limit], many=True).data)


@api_view(["GET"])
def alarm_evidence(request, alarm_id: int):
    alarm = get_object_or_404(Alarm, pk=alarm_id)
    if alarm.evidence_status != Alarm.EvidenceStatus.READY:
        return Response(
            {
                "status": alarm.evidence_status,
                "detail": alarm.evidence_error or "Evidence is not ready yet.",
            },
            status=http_status.HTTP_409_CONFLICT,
        )

    if not alarm.snapshot_object and not alarm.clip_object:
        return Response(
            {"status": alarm.evidence_status, "detail": "No evidence objects are attached to this alarm."},
            status=http_status.HTTP_404_NOT_FOUND,
        )

    def evidence_url(object_name: str) -> str:
        if object_name.startswith("local://"):
            return f"{settings.VISION_PUBLIC_URL}/evidence-files/{object_name.removeprefix('local://')}"
        return _minio_client(settings.MINIO_PUBLIC_ENDPOINT, secure=settings.MINIO_PUBLIC_SECURE).presigned_get_object(
            settings.MINIO_BUCKET, object_name, expires=expires
        )

    expires = timedelta(seconds=max(60, settings.EVIDENCE_URL_TTL_SECONDS))

    snapshot_url = (
        evidence_url(alarm.snapshot_object)
        if alarm.snapshot_object
        else ""
    )
    clip_url = (
        evidence_url(alarm.clip_object)
        if alarm.clip_object
        else ""
    )

    return Response(
        {
            "alarm_id": alarm.id,
            "status": alarm.evidence_status,
            "snapshot_url": snapshot_url,
            "clip_url": clip_url,
            "snapshot_object": alarm.snapshot_object,
            "clip_object": alarm.clip_object,
            "expires_in_seconds": max(60, settings.EVIDENCE_URL_TTL_SECONDS),
        }
    )


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

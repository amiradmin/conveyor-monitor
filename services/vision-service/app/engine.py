from .models import FrameMetrics, VisionResult


ALIGNMENT_WARNING_MM = 40.0
ALIGNMENT_STOP_MM = 80.0
TEAR_WARNING_PROBABILITY = 0.70
TEAR_STOP_PROBABILITY = 0.95


def analyze(metrics: FrameMetrics) -> VisionResult:
    offset = abs(metrics.alignment_offset_mm)
    if offset >= ALIGNMENT_STOP_MM:
        alignment_status = "CRITICAL"
    elif offset >= ALIGNMENT_WARNING_MM:
        alignment_status = "WARNING"
    else:
        alignment_status = "NORMAL"

    if metrics.tear_probability >= TEAR_STOP_PROBABILITY:
        tear_status = "CRITICAL"
    elif metrics.tear_probability >= TEAR_WARNING_PROBABILITY:
        tear_status = "WARNING"
    else:
        tear_status = "NORMAL"

    volume_m3h = metrics.material_area_m2 * metrics.belt_speed_mps * 3600.0
    stop_recommended = alignment_status == "CRITICAL" or tear_status == "CRITICAL"

    return VisionResult(
        **metrics.model_dump(),
        volume_m3h=round(volume_m3h, 2),
        alignment_status=alignment_status,
        tear_status=tear_status,
        stop_recommended=stop_recommended,
    )

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from .engine import analyze
from .models import EvidenceRequest, EvidenceResult, FrameMetrics, VisionResult
from .video_monitor import VideoMonitor

monitor = VideoMonitor()
monitors = {"CV-01": monitor, "CV-02": VideoMonitor("CV-02", os.getenv("CV02_VIDEO_SOURCE", "/data/conveyor_2.mp4"))}


def camera(conveyor_id: str) -> VideoMonitor:
    if conveyor_id not in monitors:
        raise HTTPException(status_code=404, detail="Unknown conveyor")
    return monitors[conveyor_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    for item in monitors.values():
        item.start()
    try:
        yield
    finally:
        for item in monitors.values():
            item.stop()


app = FastAPI(title="Conveyor Vision Service", version="0.3.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    diagnostics = monitor.diagnostics()
    return {
        "status": "ok" if diagnostics["source_open"] else "degraded",
        "service": "vision-service",
        "source": diagnostics["source"],
        "source_open": diagnostics["source_open"],
        "frames_processed": diagnostics["frames_processed"],
        "analyses_published": diagnostics["analyses_published"],
        "backend_pushes": diagnostics["backend_pushes"],
        "evidence_captures": diagnostics["evidence_captures"],
        "evidence_failures": diagnostics["evidence_failures"],
        "evidence_buffer_frames": diagnostics["evidence_buffer_frames"],
        "last_evidence_object": diagnostics["last_evidence_object"],
        "last_error": diagnostics["last_error"],
        "cameras": {code: item.diagnostics() for code, item in monitors.items()},
    }


@app.get("/diagnostics")
def diagnostics(conveyor_id: str = "CV-01") -> dict:
    return camera(conveyor_id).diagnostics()


@app.post("/analyze", response_model=VisionResult)
def analyze_frame(metrics: FrameMetrics) -> VisionResult:
    return analyze(metrics)


@app.get("/live", response_model=VisionResult)
def live(conveyor_id: str = "CV-01") -> VisionResult:
    latest = camera(conveyor_id).latest()
    if latest is None:
        raise HTTPException(status_code=503, detail="No analyzed video frame is available yet.")
    return latest


@app.get("/frame.jpg")
def frame(conveyor_id: str = "CV-01") -> Response:
    jpeg = camera(conveyor_id).preview()
    if jpeg is None:
        raise HTTPException(status_code=503, detail="No frame available")
    return Response(jpeg, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@app.post("/evidence", response_model=EvidenceResult)
def evidence(request: EvidenceRequest) -> EvidenceResult:
    try:
        payload = camera(request.conveyor_id).capture_evidence(request.model_dump())
        return EvidenceResult(**payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/demo", response_model=VisionResult)
def demo(conveyor_id: str = "CV-01") -> VisionResult:
    latest = camera(conveyor_id).latest()
    if latest is not None:
        return latest

    if conveyor_id != "CV-01":
        raise HTTPException(status_code=503, detail="No analyzed frame available for this conveyor")
    return analyze(
        FrameMetrics(
            conveyor_id="CV-01",
            alignment_offset_mm=0.0,
            belt_speed_mps=0.0,
            material_area_m2=0.0,
            tear_probability=0.0,
            confidence=0.0,
        )
    )

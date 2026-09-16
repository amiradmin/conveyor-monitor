from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .engine import analyze
from .models import EvidenceRequest, EvidenceResult, FrameMetrics, VisionResult
from .video_monitor import VideoMonitor

monitor = VideoMonitor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor.start()
    try:
        yield
    finally:
        monitor.stop()


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
    }


@app.get("/diagnostics")
def diagnostics() -> dict:
    return monitor.diagnostics()


@app.post("/analyze", response_model=VisionResult)
def analyze_frame(metrics: FrameMetrics) -> VisionResult:
    return analyze(metrics)


@app.get("/live", response_model=VisionResult)
def live() -> VisionResult:
    latest = monitor.latest()
    if latest is None:
        raise HTTPException(status_code=503, detail="No analyzed video frame is available yet.")
    return latest


@app.post("/evidence", response_model=EvidenceResult)
def evidence(request: EvidenceRequest) -> EvidenceResult:
    try:
        payload = monitor.capture_evidence(request.model_dump())
        return EvidenceResult(**payload)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/demo", response_model=VisionResult)
def demo() -> VisionResult:
    latest = monitor.latest()
    if latest is not None:
        return latest

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

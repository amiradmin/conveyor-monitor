from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from .engine import analyze
from .models import EvidenceRequest, EvidenceResult, FrameMetrics, VisionResult
from .fleet import MonitorFleet

monitor = MonitorFleet()

@asynccontextmanager
async def lifespan(app):
    monitor.start()
    try:
        yield
    finally:
        monitor.stop()

app = FastAPI(title="Conveyor Vision Service", version="0.4.0", lifespan=lifespan)

@app.get("/health")
def health():
    items = monitor.diagnostics()
    return {"service": "vision-service", "status": "ok" if items and all(item["source_open"] for item in items.values()) else "degraded", "conveyors": items}

@app.get("/diagnostics")
def diagnostics():
    return monitor.diagnostics()

@app.post("/analyze", response_model=VisionResult)
def analyze_frame(metrics: FrameMetrics):
    return analyze(metrics)

@app.get("/conveyors/{code}/live", response_model=VisionResult)
def conveyor_live(code: str):
    worker = monitor.get(code)
    latest = worker.latest() if worker else None
    if latest is None:
        raise HTTPException(status_code=503, detail="No analyzed video frame is available for this conveyor.")
    return latest

@app.get("/live", response_model=VisionResult)
@app.get("/demo", response_model=VisionResult)
def live():
    return conveyor_live("CV-01")

@app.post("/evidence", response_model=EvidenceResult)
def evidence(request: EvidenceRequest):
    worker = monitor.get(request.conveyor_id)
    if worker is None:
        raise HTTPException(status_code=503, detail="No video monitor is available for this conveyor.")
    try:
        return EvidenceResult(**worker.capture_evidence(request.model_dump()))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/evidence-files/{object_path:path}")
def local_evidence_file(object_path: str):
    root = Path(os.getenv("LOCAL_EVIDENCE_DIR", "/tmp/conveyor-evidence")).resolve()
    candidate = (root / object_path).resolve()
    if root not in candidate.parents or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Evidence file not found.")
    media_type = "image/jpeg" if candidate.suffix == ".jpg" else "video/mp4" if candidate.suffix == ".mp4" else "application/json"
    return FileResponse(candidate, media_type=media_type)

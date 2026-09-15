from fastapi import FastAPI
from .engine import analyze
from .models import FrameMetrics, VisionResult

app = FastAPI(title="Conveyor Vision Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "vision-service"}


@app.post("/analyze", response_model=VisionResult)
def analyze_frame(metrics: FrameMetrics) -> VisionResult:
    return analyze(metrics)


@app.get("/demo", response_model=VisionResult)
def demo() -> VisionResult:
    return analyze(
        FrameMetrics(
            conveyor_id="CV-01",
            alignment_offset_mm=12.0,
            belt_speed_mps=2.43,
            material_area_m2=0.0357,
            tear_probability=0.01,
            confidence=0.96,
        )
    )

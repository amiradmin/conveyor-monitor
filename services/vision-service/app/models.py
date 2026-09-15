from pydantic import BaseModel, Field


class FrameMetrics(BaseModel):
    conveyor_id: str = "CV-01"
    alignment_offset_mm: float = 0.0
    belt_speed_mps: float = Field(default=0.0, ge=0)
    material_area_m2: float = Field(default=0.0, ge=0)
    tear_probability: float = Field(default=0.0, ge=0, le=1)
    confidence: float = Field(default=0.0, ge=0, le=1)


class VisionResult(FrameMetrics):
    volume_m3h: float
    alignment_status: str
    tear_status: str
    stop_recommended: bool

from pydantic import BaseModel, Field


class DamageRegion(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(gt=0, le=1)
    height: float = Field(gt=0, le=1)
    score: float = Field(ge=0, le=1)


class FrameMetrics(BaseModel):
    source_revision: str = "legacy"
    conveyor_id: str = "CV-01"
    damage_regions: list[DamageRegion] = Field(default_factory=list)
    source_position_seconds: float | None = Field(default=None, ge=0)
    alignment_offset_mm: float = 0.0
    belt_speed_mps: float = Field(default=0.0, ge=0)
    material_area_m2: float = Field(default=0.0, ge=0)
    tear_probability: float = Field(default=0.0, ge=0, le=1)
    confidence: float = Field(default=0.0, ge=0, le=1)
    anomaly_score: float = Field(default=0.0, ge=0, le=1)
    anomaly_regions: list[list[float]] = Field(default_factory=list)
    detector_warming_up: bool = False


class VisionResult(FrameMetrics):
    volume_m3h: float
    alignment_status: str
    tear_status: str
    stop_recommended: bool


class EvidenceRequest(BaseModel):
    alarm_id: int
    conveyor_id: str = "CV-01"
    code: str
    severity: str
    message: str = ""
    created_at: str = ""


class EvidenceResult(BaseModel):
    bucket: str
    snapshot_object: str
    clip_object: str
    metadata_object: str
    frame_count: int

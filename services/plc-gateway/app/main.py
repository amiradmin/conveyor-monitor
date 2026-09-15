from fastapi import FastAPI
from pydantic import BaseModel, Field

from .plc import request_controlled_stop
from .settings import PLC_MODE, PLC_WRITE_ENABLED

app = FastAPI(title="Conveyor PLC Gateway", version="0.1.0")


class StopRequest(BaseModel):
    conveyor_id: str = Field(min_length=1, max_length=50)
    reason: str = Field(min_length=3, max_length=500)
    armed: bool = False


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "plc-gateway",
        "mode": PLC_MODE,
        "write_enabled": PLC_WRITE_ENABLED,
    }


@app.post("/stop-request")
def stop_request(payload: StopRequest) -> dict[str, object]:
    result = request_controlled_stop(payload.conveyor_id, payload.reason, payload.armed)
    return {
        "accepted": result.accepted,
        "executed": result.executed,
        "mode": result.mode,
        "detail": result.detail,
    }

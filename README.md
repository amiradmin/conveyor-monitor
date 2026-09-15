# Conveyor Monitor

AI-powered industrial conveyor belt monitoring platform for real-time **alignment**, **speed**, **tear/damage**, and **material volume** detection using computer vision, with PLC integration for alarms and controlled conveyor shutdown requests.

> Safety principle: AI never owns the hardwired emergency-stop function. The platform may issue a controlled `STOP_REQUEST` to a PLC only when PLC writes are explicitly enabled. Final interlocks, permissives, and safety actions remain in the PLC / Safety PLC.

## Architecture

- `backend/` — Django + Django REST Framework API, events, alarms, conveyors and camera configuration.
- `frontend/` — React + Vite operator dashboard.
- `services/vision-service/` — camera/video ingestion and computer-vision inference.
- `services/plc-gateway/` — isolated PLC integration and controlled-stop policy boundary.
- PostgreSQL — operational data and event metadata.
- Redis — cache / future realtime task transport.
- MinIO — event snapshots, clips and training assets.
- Docker Compose — local development orchestration.

## Initial capabilities

- Conveyor and camera inventory.
- Live conveyor telemetry API.
- Belt alignment offset/status model.
- Belt speed measurement model.
- Tear/damage event model.
- Material cross-section and volume-flow model.
- Alarm/event pipeline scaffold.
- PLC controlled-stop request boundary.
- Health endpoints for all services.
- Initial operations dashboard.

## Safety defaults

`PLC_WRITE_ENABLED=false` by default. In this mode the PLC gateway records and reports stop requests but does not write to a real PLC.

Emergency-stop circuits must remain independent from this application.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Then open:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/health/
- Vision service: http://localhost:8010/health
- PLC gateway: http://localhost:8020/health
- MinIO console: http://localhost:9001

## Development roadmap

1. CV-01 end-to-end simulator and dashboard.
2. RTSP camera ingestion.
3. Alignment calibration in millimetres.
4. Camera/encoder speed cross-validation.
5. Tear segmentation + temporal confirmation.
6. Volume-flow calibration.
7. PLC simulator integration.
8. Controlled-stop rule engine and operator acknowledgement.
9. Event clips and snapshots in MinIO.
10. Production hardening, observability and site deployment.

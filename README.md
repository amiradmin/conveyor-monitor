<p align="center">
  <img src="frontend/public/conveyor-logo.svg" alt="Conveyor AI Monitor" width="620" />
</p>

# Conveyor Monitor

AI-powered industrial conveyor belt monitoring platform for real-time **alignment**, **speed**, **tear/damage risk**, and **material flow** monitoring using computer vision, with PLC integration for alarms and controlled conveyor shutdown requests.

> Safety principle: AI never owns the hardwired emergency-stop function. The platform may issue a controlled `STOP_REQUEST` to a PLC only when PLC writes are explicitly enabled. Final interlocks, permissives, and safety actions remain in the PLC / Safety PLC.

## Architecture

- `backend/` — Django + Django REST Framework API, JWT auth, telemetry, events, alarms, conveyors and camera configuration.
- `frontend/` — React + Vite three-language operator dashboard (EN/FA/AR).
- `services/vision-service/` — file/camera ingestion, OpenCV telemetry extraction and alarm evidence capture.
- `services/plc-gateway/` — isolated PLC integration and controlled-stop policy boundary.
- PostgreSQL — operational telemetry and event metadata.
- Redis — cache / future realtime task transport.
- MinIO — alarm snapshots, pre-event clips, metadata and training assets.
- Docker Compose — local development orchestration.

## Current CV-01 pipeline

The development stack mounts `frontend/public/conveyor_1.mp4` into the Vision Service and loops it as the current CV-01 source. The service derives:

- belt motion from optical flow;
- material loading from calibrated texture/edge density;
- lateral material offset from the detected material centroid;
- a conservative belt-surface anomaly score used as the current tear-risk signal;
- confidence and volume-flow telemetry.

The Vision Service publishes telemetry into the Django backend through the internal ingest API. The backend persists samples in PostgreSQL, evaluates alarm thresholds, and exposes status/events to the authenticated dashboard.

When the backend creates a new alarm, evidence capture is queued without blocking telemetry ingestion. The Vision Service keeps a short JPEG ring buffer and stores three objects in the `conveyor-events` MinIO bucket:

- `snapshot.jpg` — the newest buffered frame;
- `pre_event.avi` — the seconds immediately leading up to the alarm;
- `metadata.json` — alarm details plus the latest CV telemetry.

The Alarm row stores the snapshot/clip object names and an evidence state (`PENDING`, `READY`, or `FAILED`). Operators can retry evidence capture through the alarm evidence API.

The current estimators are calibration-based CV, not a trained production tear detector. The service API is intentionally separated so trained models can replace individual estimators later without changing the frontend/backend contract.

## CV-02 belt-edge anomaly demonstration

Select **CV-02** in the dashboard header. The included `frontend/public/conveyor_2.mp4`
is a 960 × 540, 15 fps browser-friendly copy of the supplied 40-second clip.
`CV02_VIDEO_SOURCE` defaults to `/data/conveyor_2.mp4`. CV-01 retains its own source.
Both monitors run in the existing CPU OpenCV vision service; no model download is required.

CV-02 learns a healthy reference from the first 12 analyzed frames (about two
seconds at the default 6 fps). It monitors the exposed **right belt edge**,
excludes central ore, and requires a change to persist for three analyses.
The annotated image comes from the detector, so its boxes and score correspond
to the displayed frame. Camera telemetry, events, and evidence buffers stay separate.
The clip loops and the reference resets at each restart. The supplied demonstration
crosses the warning threshold near 36 seconds; alert timing also depends on
analysis rate, smoothing, and publishing intervals.

The reported value is a calibrated visual anomaly score, **not a trained tear
probability**. Boxes identify changed edge regions, not a damage segmentation.
Lighting, camera motion, occlusion, or an unhealthy startup reference can affect
results. This profile is specific to this fixed view and must be recalibrated for
another camera; hidden belt damage is outside its coverage. Speed/alignment/flow
remain illustrative calibration-based estimates. PLC writes remain disabled by default.

After updating, run `docker compose up --build -d`; Django applies the telemetry
metadata migration at startup. The CV-02 source is available in the repository;
the CV-01 development clip must still be provided as described below.

## Safety defaults

`PLC_WRITE_ENABLED=false` by default. In this mode the PLC gateway records and reports stop requests but does not write to a real PLC.

Emergency-stop circuits must remain independent from this application.

## Quick start

Place the development clip at:

```text
frontend/public/conveyor_1.mp4
```

Then:

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8001/api/health/
- Vision service: http://localhost:8010/health
- Vision live telemetry: http://localhost:8010/live
- PLC gateway: http://localhost:8020/health
- MinIO console: http://localhost:9001

## Development roadmap

1. CV-01 file-based end-to-end telemetry and dashboard — operational.
2. RTSP camera ingestion and reconnect policy.
3. Site calibration for alignment and material cross-section.
4. Camera/encoder speed cross-validation.
5. Trained tear/damage segmentation + temporal confirmation.
6. Volume-flow calibration against belt scale / plant instrumentation.
7. PLC simulator and read-only tag integration.
8. Controlled-stop rule engine and operator acknowledgement.
9. Alarm snapshots + pre-event clips in MinIO — operational for CV-01.
10. Production hardening, durable background jobs, observability, backups, HTTPS and site deployment.

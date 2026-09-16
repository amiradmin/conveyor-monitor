from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import requests

from .engine import analyze
from .models import FrameMetrics, VisionResult


@dataclass
class MonitorDiagnostics:
    source: str
    running: bool = False
    source_open: bool = False
    frames_processed: int = 0
    analyses_published: int = 0
    backend_pushes: int = 0
    last_backend_status: int | None = None
    last_error: str = ""
    fps: float = 0.0
    width: int = 0
    height: int = 0


class VideoMonitor:
    """Continuously analyze a file/camera source and expose the latest telemetry.

    The current implementation is deliberately calibration-based rather than a
    trained defect model. It derives motion from optical flow, material loading
    from texture/edge density, lateral offset from the material centroid and a
    conservative belt-surface anomaly score for tear risk. The interfaces are
    intentionally stable so trained CV models can replace individual estimators
    later without changing the API or dashboard contract.
    """

    def __init__(self) -> None:
        self.source = os.getenv("VISION_VIDEO_SOURCE", "/data/conveyor_1.mp4")
        self.loop = os.getenv("VISION_LOOP", "true").lower() == "true"
        self.publish_hz = max(0.2, float(os.getenv("VISION_PUBLISH_HZ", "2")))
        self.processing_width = max(320, int(os.getenv("VISION_PROCESSING_WIDTH", "480")))
        self.belt_width_mm = float(os.getenv("VISION_BELT_WIDTH_MM", "1200"))
        self.speed_scale = float(os.getenv("VISION_SPEED_SCALE", "0.063"))
        self.material_area_edge_scale = float(os.getenv("VISION_MATERIAL_AREA_EDGE_SCALE", "0.158"))
        self.alignment_zero_x = float(os.getenv("VISION_ALIGNMENT_ZERO_X", "0.500"))
        self.backend_ingest_url = os.getenv(
            "BACKEND_INGEST_URL", "http://backend:8000/api/telemetry/ingest/"
        )
        self.internal_token = os.getenv("INTERNAL_SERVICE_TOKEN", "dev-internal-token")
        self.push_interval = max(0.5, float(os.getenv("VISION_PUSH_INTERVAL_SECONDS", "2")))

        self._latest: VisionResult | None = None
        self._latest_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._prev_gray: np.ndarray | None = None
        self._smoothed: dict[str, float] = {}
        self._last_publish = 0.0
        self._last_push = 0.0
        self._diagnostics = MonitorDiagnostics(source=self.source)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="vision-video-monitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def latest(self) -> VisionResult | None:
        with self._latest_lock:
            return self._latest.model_copy(deep=True) if self._latest else None

    def diagnostics(self) -> dict[str, Any]:
        return dict(self._diagnostics.__dict__)

    def _open_source(self) -> cv2.VideoCapture:
        source: str | int = self.source
        if self.source.isdigit() and not Path(self.source).exists():
            source = int(self.source)
        capture = cv2.VideoCapture(source)
        if not capture.isOpened():
            raise RuntimeError(f"Unable to open vision source: {self.source}")
        return capture

    def _run(self) -> None:
        self._diagnostics.running = True
        while not self._stop.is_set():
            capture: cv2.VideoCapture | None = None
            try:
                capture = self._open_source()
                self._diagnostics.source_open = True
                self._diagnostics.last_error = ""
                fps = capture.get(cv2.CAP_PROP_FPS) or 24.0
                if not np.isfinite(fps) or fps < 1:
                    fps = 24.0
                self._diagnostics.fps = round(float(fps), 3)
                self._diagnostics.width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
                self._diagnostics.height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
                frame_sleep = 1.0 / fps if Path(self.source).is_file() else 0.0
                self._prev_gray = None

                while not self._stop.is_set():
                    started = time.monotonic()
                    ok, frame = capture.read()
                    if not ok:
                        if self.loop and Path(self.source).is_file():
                            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            self._prev_gray = None
                            continue
                        raise RuntimeError("Vision source stopped returning frames")

                    self._diagnostics.frames_processed += 1
                    metrics = self._estimate_metrics(frame, fps)

                    now = time.monotonic()
                    if now - self._last_publish >= 1.0 / self.publish_hz:
                        result = analyze(metrics)
                        with self._latest_lock:
                            self._latest = result
                        self._last_publish = now
                        self._diagnostics.analyses_published += 1

                        if now - self._last_push >= self.push_interval:
                            self._push_backend(result)
                            self._last_push = now

                    if frame_sleep:
                        elapsed = time.monotonic() - started
                        if elapsed < frame_sleep:
                            time.sleep(frame_sleep - elapsed)

            except Exception as exc:  # keep service alive and retry cameras/files
                self._diagnostics.last_error = str(exc)
                self._diagnostics.source_open = False
                time.sleep(2.0)
            finally:
                if capture is not None:
                    capture.release()

        self._diagnostics.running = False
        self._diagnostics.source_open = False

    def _resize_gray(self, frame: np.ndarray) -> np.ndarray:
        height, width = frame.shape[:2]
        target_width = min(width, self.processing_width)
        scale = target_width / width
        target_height = max(1, int(height * scale))
        resized = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
        return cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def _belt_mask(height: int, width: int) -> np.ndarray:
        mask = np.zeros((height, width), dtype=np.uint8)
        polygon = np.array(
            [
                [int(0.44 * width), int(0.08 * height)],
                [int(0.56 * width), int(0.08 * height)],
                [int(0.73 * width), height - 1],
                [int(0.27 * width), height - 1],
            ],
            dtype=np.int32,
        )
        cv2.fillPoly(mask, [polygon], 255)
        return mask

    @staticmethod
    def _material_core_mask(height: int, width: int) -> np.ndarray:
        mask = np.zeros((height, width), dtype=np.uint8)
        polygon = np.array(
            [
                [int(0.47 * width), int(0.09 * height)],
                [int(0.53 * width), int(0.09 * height)],
                [int(0.60 * width), height - 1],
                [int(0.40 * width), height - 1],
            ],
            dtype=np.int32,
        )
        cv2.fillPoly(mask, [polygon], 255)
        return mask

    def _ema(self, name: str, value: float, alpha: float = 0.18) -> float:
        previous = self._smoothed.get(name)
        filtered = value if previous is None else (alpha * value + (1.0 - alpha) * previous)
        self._smoothed[name] = filtered
        return filtered

    def _estimate_metrics(self, frame: np.ndarray, source_fps: float) -> FrameMetrics:
        gray = self._resize_gray(frame)
        height, width = gray.shape
        belt_mask = self._belt_mask(height, width)
        valid = belt_mask > 0

        edges = cv2.Canny(gray, 80, 160)
        material_edges = (edges > 0) & valid
        edge_density = float(material_edges.sum() / max(1, valid.sum()))

        # Material cross-section calibration. For the current CV-01 camera, the
        # generated reference clip sits around 0.035 m². A per-site calibration
        # value can override this conversion without changing the pipeline.
        material_area = float(np.clip(edge_density * self.material_area_edge_scale, 0.002, 0.09))

        ys, xs = np.where(material_edges)
        if len(xs) >= 25:
            centroid_x = float(xs.mean() / width)
        else:
            centroid_x = self.alignment_zero_x
        average_belt_fraction = 0.32
        lateral_fraction = (centroid_x - self.alignment_zero_x) / average_belt_fraction
        alignment_mm = float(np.clip(lateral_fraction * self.belt_width_mm, -120.0, 120.0))

        speed_mps = self._smoothed.get("speed_mps", 2.4)
        if self._prev_gray is not None and self._prev_gray.shape == gray.shape:
            flow = cv2.calcOpticalFlowFarneback(
                self._prev_gray,
                gray,
                None,
                0.5,
                3,
                15,
                3,
                5,
                1.2,
                0,
            )
            magnitude = np.linalg.norm(flow, axis=2)
            flow_values = magnitude[valid]
            if flow_values.size:
                median_flow = float(np.median(flow_values))
                # Scale flow back to a 640px reference width, then convert the
                # per-frame displacement into pixels/second and calibrated m/s.
                reference_flow = median_flow * (640.0 / width)
                measured_speed = reference_flow * source_fps * self.speed_scale
                speed_mps = float(np.clip(measured_speed, 0.0, 4.5))
        self._prev_gray = gray

        core_mask = self._material_core_mask(height, width)
        shoulder = valid & (core_mask == 0)
        shoulder_edge_density = float(((edges > 0) & shoulder).sum() / max(1, shoulder.sum()))
        # The normal reference belt shoulders measure ~0.14 edge density. Keep
        # normal operation near 1% and increase only when surface structure on
        # the belt shoulders changes substantially.
        tear_probability = float(np.clip(0.01 + max(0.0, shoulder_edge_density - 0.17) * 4.0, 0.01, 0.99))

        texture_quality = float(np.clip(edge_density / 0.22, 0.0, 1.0))
        confidence = float(np.clip(0.88 + 0.09 * texture_quality, 0.0, 0.98))

        return FrameMetrics(
            conveyor_id="CV-01",
            alignment_offset_mm=round(self._ema("alignment_mm", alignment_mm), 2),
            belt_speed_mps=round(self._ema("speed_mps", speed_mps), 3),
            material_area_m2=round(self._ema("material_area", material_area), 5),
            tear_probability=round(self._ema("tear_probability", tear_probability), 4),
            confidence=round(self._ema("confidence", confidence), 4),
        )

    def _push_backend(self, result: VisionResult) -> None:
        payload = {
            "conveyor_id": result.conveyor_id,
            "belt_speed_mps": result.belt_speed_mps,
            "alignment_offset_mm": result.alignment_offset_mm,
            "volume_m3h": result.volume_m3h,
            "tear_probability": result.tear_probability,
            "confidence": result.confidence,
        }
        try:
            response = requests.post(
                self.backend_ingest_url,
                json=payload,
                headers={"X-Internal-Token": self.internal_token},
                timeout=2.0,
            )
            self._diagnostics.last_backend_status = response.status_code
            if 200 <= response.status_code < 300:
                self._diagnostics.backend_pushes += 1
            else:
                self._diagnostics.last_error = f"Backend ingest returned HTTP {response.status_code}"
        except requests.RequestException as exc:
            self._diagnostics.last_error = f"Backend ingest failed: {exc}"

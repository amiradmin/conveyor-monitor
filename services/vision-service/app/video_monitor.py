from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import cv2
import numpy as np
import requests
from minio import Minio

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
    evidence_captures: int = 0
    evidence_failures: int = 0
    last_evidence_object: str = ""
    last_error: str = ""
    fps: float = 0.0
    width: int = 0
    height: int = 0


class VideoMonitor:
    """Continuously analyze a video source and retain short alarm evidence.

    The current estimators are calibration-based. Motion comes from optical
    flow, loading from image texture, alignment from calibrated belt boundaries and
    tear risk from belt-shoulder structure. A small JPEG ring buffer is kept so
    a new alarm can immediately persist a snapshot plus the few seconds leading
    up to the event in MinIO.
    """

    def __init__(self, source=None, conveyor_id="CV-01", belt_width_mm=None, source_revision="legacy") -> None:
        self.source_revision = source_revision
        self.conveyor_id = conveyor_id
        self.source = source or os.getenv("VISION_VIDEO_SOURCE", "/data/conveyor_1.mp4")
        self.loop = os.getenv("VISION_LOOP", "true").lower() == "true"
        self.publish_hz = max(0.2, float(os.getenv("VISION_PUBLISH_HZ", "2")))
        self.analysis_fps = max(self.publish_hz, float(os.getenv("VISION_ANALYSIS_FPS", "6")))
        self.processing_width = max(320, int(os.getenv("VISION_PROCESSING_WIDTH", "480")))
        self.belt_width_mm = float(belt_width_mm or os.getenv("VISION_BELT_WIDTH_MM", "1200"))
        self.speed_scale = float(os.getenv("VISION_SPEED_SCALE", "0.063"))
        self.material_area_edge_scale = float(os.getenv("VISION_MATERIAL_AREA_EDGE_SCALE", "0.158"))
        self.edge_geometry = tuple(float(os.getenv(name, default)) for name, default in (
            ("VISION_LEFT_EDGE_TOP", "0.27"), ("VISION_LEFT_EDGE_BOTTOM", "0.07"),
            ("VISION_RIGHT_EDGE_TOP", "0.68"), ("VISION_RIGHT_EDGE_BOTTOM", "0.88"),
        ))
        self.alignment_zero_mm = float(os.getenv("VISION_ALIGNMENT_ZERO_MM", "0"))
        self.backend_ingest_url = os.getenv(
            "BACKEND_INGEST_URL", "http://backend:8000/api/telemetry/ingest/"
        )
        self.internal_token = os.getenv("INTERNAL_SERVICE_TOKEN", "dev-internal-token")
        self.push_interval = max(0.5, float(os.getenv("VISION_PUSH_INTERVAL_SECONDS", "2")))

        self.evidence_seconds = max(2, int(os.getenv("EVIDENCE_SECONDS", "6")))
        self.evidence_fps = max(2, int(os.getenv("EVIDENCE_FPS", "6")))
        self.evidence_width = max(320, int(os.getenv("EVIDENCE_WIDTH", "960")))
        self.evidence_jpeg_quality = min(95, max(50, int(os.getenv("EVIDENCE_JPEG_QUALITY", "82"))))
        self.evidence_video_encoder = os.getenv("EVIDENCE_VIDEO_ENCODER", "auto").strip().lower()
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        self.minio_access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
        self.minio_secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")
        self.minio_bucket = os.getenv("MINIO_BUCKET", "conveyor-events")
        self.local_evidence_dir = Path(
            os.getenv("LOCAL_EVIDENCE_DIR", "/tmp/conveyor-evidence")
        ).resolve()

        self._latest: VisionResult | None = None
        self._latest_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._prev_gray: np.ndarray | None = None
        self._smoothed: dict[str, float] = {}
        self._last_publish = 0.0
        self._last_analysis = 0.0
        self._last_push = 0.0
        self._last_evidence_frame = 0.0
        self._evidence_lock = threading.Lock()
        self._evidence_frames: deque[bytes] = deque(
            maxlen=self.evidence_seconds * self.evidence_fps
        )
        self._diagnostics = MonitorDiagnostics(source=self.source)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name=f"vision-{self.conveyor_id}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def latest(self) -> VisionResult | None:
        with self._latest_lock:
            return self._latest.model_copy(deep=True) if self._latest else None

    def diagnostics(self) -> dict[str, Any]:
        data = dict(self._diagnostics.__dict__)
        with self._evidence_lock:
            data["evidence_buffer_frames"] = len(self._evidence_frames)
        data["evidence_buffer_seconds"] = self.evidence_seconds
        data["analysis_fps"] = self.analysis_fps
        data["evidence_fps"] = self.evidence_fps
        data["minio_bucket"] = self.minio_bucket
        return data

    def capture_evidence(self, alarm: dict[str, Any]) -> dict[str, Any]:
        if alarm.get("conveyor_id", "CV-01") != self.conveyor_id:
            raise ValueError("Evidence belongs to a different conveyor.")
        with self._evidence_lock:
            frames = list(self._evidence_frames)

        if not frames:
            self._diagnostics.evidence_failures += 1
            raise RuntimeError("Evidence buffer is empty; no video frame is available yet.")

        alarm_id = int(alarm["alarm_id"])
        conveyor_id = str(alarm.get("conveyor_id", "CV-01"))
        code = str(alarm.get("code", "ALARM"))
        safe_code = "".join(ch.lower() if ch.isalnum() else "-" for ch in code).strip("-") or "alarm"
        now = datetime.now(timezone.utc)
        prefix = (
            f"{conveyor_id}/{now:%Y/%m/%d}/"
            f"alarm-{alarm_id:06d}-{safe_code}"
        )
        snapshot_object = f"{prefix}/snapshot.jpg"
        clip_object = f"{prefix}/pre_event.mp4"
        metadata_object = f"{prefix}/metadata.json"

        snapshot = frames[-1]
        clip_path = self._write_evidence_clip(frames)
        latest = self.latest()

        def metadata_for(snapshot_ref: str, clip_ref: str) -> bytes:
            return json.dumps(
                {
                    "alarm": alarm,
                    "captured_at": now.isoformat(),
                    "frame_count": len(frames),
                    "evidence_seconds": self.evidence_seconds,
                    "evidence_fps": self.evidence_fps,
                    "source": self.source,
                    "vision": latest.model_dump() if latest else None,
                    "snapshot_object": snapshot_ref,
                    "clip_object": clip_ref,
                },
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8")

        try:
            client = self._minio_client()
            if not client.bucket_exists(self.minio_bucket):
                client.make_bucket(self.minio_bucket)
            client.put_object(
                self.minio_bucket,
                snapshot_object,
                BytesIO(snapshot),
                length=len(snapshot),
                content_type="image/jpeg",
            )
            client.fput_object(
                self.minio_bucket,
                clip_object,
                clip_path,
                content_type="video/mp4",
            )
            metadata_bytes = metadata_for(snapshot_object, clip_object)
            client.put_object(
                self.minio_bucket,
                metadata_object,
                BytesIO(metadata_bytes),
                length=len(metadata_bytes),
                content_type="application/json",
            )
            bucket = self.minio_bucket
        except Exception:
            # Keep demo and edge deployments useful when object storage is down.
            # These files are exposed only by the local vision service endpoint.
            evidence_dir = (self.local_evidence_dir / prefix).resolve()
            if self.local_evidence_dir not in evidence_dir.parents:
                raise RuntimeError("Invalid local evidence path")
            evidence_dir.mkdir(parents=True, exist_ok=True)
            (evidence_dir / "snapshot.jpg").write_bytes(snapshot)
            shutil.move(clip_path, evidence_dir / "pre_event.mp4")
            snapshot_object = f"local://{prefix}/snapshot.jpg"
            clip_object = f"local://{prefix}/pre_event.mp4"
            metadata_object = f"local://{prefix}/metadata.json"
            (evidence_dir / "metadata.json").write_bytes(metadata_for(snapshot_object, clip_object))
            bucket = "local"
        finally:
            try:
                os.unlink(clip_path)
            except OSError:
                pass

        self._diagnostics.evidence_captures += 1
        self._diagnostics.last_evidence_object = snapshot_object
        return {
            "bucket": bucket,
            "snapshot_object": snapshot_object,
            "clip_object": clip_object,
            "metadata_object": metadata_object,
            "frame_count": len(frames),
        }

    def _minio_client(self) -> Minio:
        raw = self.minio_endpoint.strip()
        secure = False
        endpoint = raw
        if "://" in raw:
            parsed = urlparse(raw)
            secure = parsed.scheme == "https"
            endpoint = parsed.netloc
        return Minio(
            endpoint,
            access_key=self.minio_access_key,
            secret_key=self.minio_secret_key,
            secure=secure,
        )

    def _write_evidence_clip(self, frames: list[bytes]) -> str:
        if not frames:
            self._diagnostics.evidence_failures += 1
            raise RuntimeError("Unable to encode an empty evidence clip.")

        handle = tempfile.NamedTemporaryFile(prefix="conveyor-evidence-", suffix=".mp4", delete=False)
        path = handle.name
        handle.close()

        encoder = self._evidence_encoder()
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "image2pipe",
            "-vcodec",
            "mjpeg",
            "-framerate",
            str(self.evidence_fps),
            "-i",
            "pipe:0",
            "-an",
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v",
            encoder,
        ]
        if encoder == "h264_nvenc":
            command += ["-preset", "p4", "-cq", "23"]
        else:
            command += ["-preset", "veryfast", "-crf", "23"]
        command += [
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            path,
        ]
        try:
            completed = subprocess.run(
                command,
                input=b"".join(frames),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=max(15, self.evidence_seconds * 4),
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            try:
                os.unlink(path)
            except OSError:
                pass
            self._diagnostics.evidence_failures += 1
            raise RuntimeError(f"Unable to run ffmpeg for evidence encoding: {exc}") from exc

        if completed.returncode != 0 or not os.path.exists(path) or os.path.getsize(path) == 0:
            error = completed.stderr.decode("utf-8", errors="replace")[-500:]
            try:
                os.unlink(path)
            except OSError:
                pass
            self._diagnostics.evidence_failures += 1
            raise RuntimeError(f"ffmpeg evidence encoding failed: {error}")
        return path

    def _evidence_encoder(self) -> str:
        """Prefer NVENC when the NVIDIA runtime is available, otherwise use CPU x264."""
        configured = self.evidence_video_encoder
        if configured in {"libx264", "h264_nvenc"}:
            return configured
        if configured not in {"", "auto"}:
            raise RuntimeError(
                "EVIDENCE_VIDEO_ENCODER must be auto, h264_nvenc, or libx264"
            )
        if Path("/dev/nvidia0").exists() or Path("/dev/nvidiactl").exists():
            return "h264_nvenc"
        return "libx264"

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
                    now = time.monotonic()
                    self._buffer_evidence_frame(frame, now)

                    if now - self._last_analysis < 1.0 / self.analysis_fps:
                        if frame_sleep:
                            elapsed = time.monotonic() - started
                            if elapsed < frame_sleep:
                                time.sleep(frame_sleep - elapsed)
                        continue

                    analysis_interval = (
                        now - self._last_analysis if self._last_analysis > 0 else 1.0 / self.analysis_fps
                    )
                    self._last_analysis = now
                    effective_fps = 1.0 / max(analysis_interval, 1e-6)
                    metrics = self._estimate_metrics(frame, effective_fps)
                    if Path(self.source).is_file():
                        metrics.source_position_seconds = max(0.0, capture.get(cv2.CAP_PROP_POS_MSEC) / 1000.0)

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

            except Exception as exc:
                self._diagnostics.last_error = str(exc)
                self._diagnostics.source_open = False
                with self._latest_lock:
                    self._latest = None
                self._stop.wait(2.0)
            finally:
                if capture is not None:
                    capture.release()

        self._diagnostics.running = False
        self._diagnostics.source_open = False

    def _buffer_evidence_frame(self, frame: np.ndarray, now: float) -> None:
        if now - self._last_evidence_frame < 1.0 / self.evidence_fps:
            return
        self._last_evidence_frame = now

        height, width = frame.shape[:2]
        target_width = min(width, self.evidence_width)
        scale = target_width / width
        target_height = max(1, int(height * scale))
        resized = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
        ok, encoded = cv2.imencode(
            ".jpg",
            resized,
            [int(cv2.IMWRITE_JPEG_QUALITY), self.evidence_jpeg_quality],
        )
        if not ok:
            return
        with self._evidence_lock:
            self._evidence_frames.append(encoded.tobytes())

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

    def _inspect_belt_edges(self, gray: np.ndarray, edges: np.ndarray) -> tuple[float, float]:
        """Camera-calibrated edge texture screening, not a trained defect classifier.

        Inspect short edge strips so a localized fray is not diluted by the
        entire belt. Track boundary gradients rather than the ore centroid.
        Coordinates are normalized for the supplied fixed-camera video.
        """
        height, width = gray.shape
        gradient = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
        displacements = []
        densities = []
        self._damage_regions = []
        step = max(1, int(height / 12))
        lt, lb, rt, rb = self.edge_geometry
        for top, bottom in ((lt, lb), (rt, rb)):
            side_offsets = []
            side_densities = []
            candidates = []
            # Open left-edge notches have less fine texture than frayed fibres.
            # Healthy left strips remain below 0.12 in the reference video;
            # keep the higher right-side threshold for its different background.
            detection_density = 0.12 if top < 0.5 else 0.15
            for y in range(int(height / 6), int(height * 5 / 6), step):
                expected = (top + (bottom - top) * y / height) * width
                radius = max(2, int(width * 0.025))
                x0, x1 = max(0, int(expected) - radius), min(width, int(expected) + radius + 1)
                profile = np.median(gradient[y:y + step, x0:x1], axis=0)
                if profile.size and float(profile.max()) > 40:
                    side_offsets.append((x0 + int(profile.argmax()) - expected) / width)
                # The right-hand tear opens across the nominal boundary.
                # Include its outer lip rather than sampling only intact rubber
                # inside the belt. Keep the same narrow total strip width.
                left = int(expected) if top < 0.5 else int(expected) - int(width * 0.03)
                patch = edges[y:y + step, max(0, left):min(width, left + int(width * 0.05))]
                if patch.size:
                    density = float(np.mean(patch > 0))
                    side_densities.append(density)
                    if density >= detection_density:
                        candidates.append((max(0, left) / width, y / height,
                                           min(1, (left + int(width * 0.05)) / width),
                                           min(1, (y + step) / height)))
            if len(side_offsets) >= 3:
                displacements.append(float(np.median(side_offsets)))
            if len(side_densities) >= 2:
                # Two affected strips reject a single isolated texture spike.
                density = sorted(side_densities)[-2]
                densities.append(density)
                if density >= detection_density and len(candidates) >= 2:
                    x0 = min(box[0] for box in candidates)
                    y0 = min(box[1] for box in candidates)
                    x1 = max(box[2] for box in candidates)
                    y1 = max(box[3] for box in candidates)
                    self._damage_regions.append(dict(x=x0, y=y0, width=x1-x0, height=y1-y0,
                                                     score=float(np.clip((density - 0.08) * 5, 0, 0.99))))
        displacement = float(np.median(displacements)) if displacements else 0.0
        belt_fraction = max(0.01, ((rt - lt) + (rb - lb)) / 2)
        offset = float(np.clip(displacement * self.belt_width_mm / belt_fraction - self.alignment_zero_mm, -120, 120))
        damage = float(np.clip((max(densities, default=0.0) - 0.08) * 5, 0.01, 0.99))
        return offset, damage

    def _estimate_metrics(self, frame: np.ndarray, source_fps: float) -> FrameMetrics:
        gray = self._resize_gray(frame)
        height, width = gray.shape
        belt_mask = self._belt_mask(height, width)
        valid = belt_mask > 0

        edges = cv2.Canny(gray, 80, 160)
        material_edges = (edges > 0) & valid
        edge_density = float(material_edges.sum() / max(1, valid.sum()))
        material_area = float(np.clip(edge_density * self.material_area_edge_scale, 0.002, 0.09))

        alignment_mm, edge_damage = self._inspect_belt_edges(gray, edges)

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
                reference_flow = median_flow * (640.0 / width)
                measured_speed = reference_flow * source_fps * self.speed_scale
                speed_mps = float(np.clip(measured_speed, 0.0, 4.5))
        self._prev_gray = gray

        tear_probability = edge_damage

        texture_quality = float(np.clip(edge_density / 0.22, 0.0, 1.0))
        confidence = float(np.clip(0.88 + 0.09 * texture_quality, 0.0, 0.98))

        return FrameMetrics(
            conveyor_id=self.conveyor_id,
            source_revision=self.source_revision,
            damage_regions=self._damage_regions,
            alignment_offset_mm=round(self._ema("alignment_mm", alignment_mm), 2),
            belt_speed_mps=round(self._ema("speed_mps", speed_mps), 3),
            material_area_m2=round(self._ema("material_area", material_area), 5),
            tear_probability=round(self._ema("tear_probability", tear_probability, alpha=0.65), 4),
            confidence=round(self._ema("confidence", confidence), 4),
        )

    def _push_backend(self, result: VisionResult) -> None:
        payload = {
            "conveyor_id": result.conveyor_id,
            "source_revision": self.source_revision,
            "damage_regions": [region.model_dump() for region in result.damage_regions],
            "source_position_seconds": result.source_position_seconds,
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
                self._diagnostics.last_error = ""
            else:
                self._diagnostics.last_error = f"Backend ingest returned HTTP {response.status_code}"
        except requests.RequestException as exc:
            self._diagnostics.last_error = f"Backend ingest failed: {exc}"

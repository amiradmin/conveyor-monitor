from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.belt_anomaly import BeltAnomalyDetector
from app.main import app, monitors
from app.video_monitor import VideoMonitor


def test_static_healthy_frames_do_not_trigger():
    detector = BeltAnomalyDetector(warmup_frames=3)
    frame = np.full((270, 480), 110, dtype=np.uint8)
    for _ in range(15):
        assert detector.detect(frame)["score"] == 0


def test_persistent_edge_defect_and_recovery():
    detector = BeltAnomalyDetector(warmup_frames=3)
    frame = np.full((270, 480), 110, dtype=np.uint8)
    for _ in range(3):
        detector.detect(frame)
    damaged = frame.copy()
    cv2.rectangle(damaged, (370, 110), (380, 150), 0, -1)
    assert detector.detect(damaged)["score"] == 0
    assert detector.detect(damaged)["score"] == 0
    result = detector.detect(damaged)
    assert result["score"] > .35
    assert result["regions"]
    assert detector.detect(frame)["score"] == 0
    detector.reset()
    assert detector.detect(damaged)["warming_up"]


def test_ore_changes_outside_edge_are_ignored():
    detector = BeltAnomalyDetector(warmup_frames=3)
    frame = np.full((270, 480), 110, dtype=np.uint8)
    for _ in range(3):
        detector.detect(frame)
    frame[80:200, 180:270] = 0
    for _ in range(6):
        assert detector.detect(frame)["score"] == 0


def test_camera_api_does_not_return_cv01_frame_for_cv02():
    client = TestClient(app)
    with patch.object(monitors["CV-01"], "preview", return_value=b"first"), patch.object(monitors["CV-02"], "preview", return_value=b"second"):
        assert client.get("/frame.jpg?conveyor_id=CV-02").content == b"second"
        assert client.get("/frame.jpg?conveyor_id=CV-01").content == b"first"
        assert client.get("/frame.jpg?conveyor_id=CV-99").status_code == 404
    with patch.object(monitors["CV-02"], "latest", return_value=None):
        assert client.get("/live?conveyor_id=CV-02").status_code == 503


def test_evidence_uses_the_requested_camera_buffer():
    client = TestClient(app)
    evidence = {"bucket": "conveyor-events", "snapshot_object": "CV-02/snapshot.jpg",
                "clip_object": "CV-02/pre_event.mp4", "metadata_object": "CV-02/metadata.json", "frame_count": 10}
    with patch.object(monitors["CV-01"], "capture_evidence") as first, patch.object(monitors["CV-02"], "capture_evidence", return_value=evidence) as second:
        response = client.post('/evidence', json={"conveyor_id": "CV-02", "alarm_id": 1, "code": "BELT_ANOMALY_WARNING", "severity": "WARNING"})
        assert response.status_code == 200
        assert response.json()["snapshot_object"].startswith("CV-02/")
        first.assert_not_called()
        second.assert_called_once()


def test_monitor_reports_cv02_score_without_cross_camera_id():
    monitor = VideoMonitor("CV-02", "unused.mp4")
    frame = np.full((270, 480, 3), 110, dtype=np.uint8)
    for _ in range(12):
        monitor._estimate_metrics(frame, 6)
    cv2.rectangle(frame, (370, 110), (380, 150), (0, 0, 0), -1)
    for _ in range(3):
        result = monitor._estimate_metrics(frame, 6)
    assert result.conveyor_id == "CV-02"
    assert result.tear_probability == result.anomaly_score > .35
    assert not result.detector_warming_up


def test_uploaded_video_opens_and_later_damage_is_detected():
    video = Path(__file__).resolve().parents[3] / "frontend/public/conveyor_2.mp4"
    capture = cv2.VideoCapture(str(video))
    assert capture.isOpened()
    detector = BeltAnomalyDetector()
    scores = []
    for index in range(240):
        capture.set(cv2.CAP_PROP_POS_MSEC, index * 1000 / 6)
        ok, frame = capture.read()
        if not ok:
            break
        gray = cv2.cvtColor(cv2.resize(frame, (480, 270)), cv2.COLOR_BGR2GRAY)
        scores.append(detector.detect(gray)["score"])
    capture.release()
    assert len(scores) >= 230
    assert max(scores[35 * 6:]) >= .65

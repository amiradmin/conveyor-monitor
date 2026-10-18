"""Calibrated edge-change detector for the fixed CV-02 demonstration camera.

Scores are visual anomaly scores, not trained tear probabilities. The first
two seconds must show a healthy edge. Material in the middle is excluded.
"""
from __future__ import annotations

import cv2
import numpy as np


class BeltAnomalyDetector:
    def __init__(self, warmup_frames: int = 12) -> None:
        self.warmup_frames = warmup_frames
        self.reset()

    def reset(self) -> None:
        self._warmup: list[np.ndarray] = []
        self._reference: np.ndarray | None = None
        self._hits = 0

    def detect(self, gray: np.ndarray) -> dict:
        height, width = gray.shape
        smooth = cv2.GaussianBlur(gray, (5, 5), 0)
        if self._reference is None:
            self._warmup.append(smooth)
            if len(self._warmup) >= self.warmup_frames:
                self._reference = np.median(self._warmup, axis=0).astype(np.uint8)
                self._warmup.clear()
            return {"score": 0.0, "regions": [], "warming_up": True}

        mask = np.zeros_like(gray)
        # Exposed right edge for this camera; exclude central ore and rails.
        for points in (
            [(.675, .05), (.715, .05), (.895, .95), (.855, .95)],
        ):
            polygon = np.array([(int(x * width), int(y * height)) for x, y in points], np.int32)
            cv2.fillPoly(mask, [polygon], 255)
        diff = cv2.absdiff(smooth, self._reference)
        changed = ((diff > 28) & (mask > 0)).astype(np.uint8) * 255
        changed = cv2.morphologyEx(changed, cv2.MORPH_CLOSE, np.ones((5, 3), np.uint8))
        contours, _ = cv2.findContours(changed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regions = []
        largest = 0.0
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            if area < width * height * .00035 or h < height * .035 or w < width * .008:
                continue
            largest = max(largest, area / (width * height))
            regions.append([round(x / width, 4), round(y / height, 4), round(w / width, 4), round(h / height, 4)])
        self._hits = self._hits + 1 if regions else 0
        confirmed = self._hits >= 3
        score = min(.99, largest / .004) if confirmed else 0.0
        return {"score": round(score, 4), "regions": regions if confirmed else [], "warming_up": False}

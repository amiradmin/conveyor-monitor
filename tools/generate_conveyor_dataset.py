#!/usr/bin/env python3
"""Generate a small synthetic conveyor dataset without Blender.

Each run writes an MP4 plus one JSONL label per frame. The renderer is deliberately
simple and deterministic enough for smoke tests; use it to bootstrap the pipeline,
then mix in real camera footage when available.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np


def render_frame(width: int, height: int, frame: int, fps: int, scenario: str, seed: int):
    rng = np.random.default_rng(seed + frame)
    image = np.zeros((height, width, 3), dtype=np.uint8)
    # Industrial background and safety rails.
    image[:] = (24, 35, 47)
    cv2.rectangle(image, (0, 0), (width, height), (17, 28, 40), -1)
    cv2.line(image, (int(width * .08), 0), (int(width * .08), height), (65, 74, 82), 10)
    cv2.line(image, (int(width * .92), 0), (int(width * .92), height), (65, 74, 82), 10)
    cv2.line(image, (int(width * .10), int(height * .2)), (int(width * .9), int(height * .2)), (34, 124, 181), 4)

    # Trapezoid belt, slightly shifting to make alignment measurable.
    drift = 0.035 * math.sin(frame / fps * 0.8) if scenario == "normal" else 0.12 + frame / max(1, fps * 10) * .08
    cx = width * (.5 + drift)
    top_w, bottom_w = width * .23, width * .72
    pts = np.array([[cx - top_w / 2, 0], [cx + top_w / 2, 0], [cx + bottom_w / 2, height], [cx - bottom_w / 2, height]], np.int32)
    cv2.fillConvexPoly(image, pts, (57, 64, 68))
    cv2.polylines(image, [pts], True, (132, 143, 146), 2)

    # Material stones. Overload increases density and width beyond the nominal zone.
    overload = scenario == "overload"
    spill = scenario == "material_spill"
    stone_count = 36 if not overload else 88
    if spill:
        stone_count = 58
    for _ in range(stone_count):
        y = int(rng.uniform(18, height + 20))
        t = y / height
        belt_half = (top_w + (bottom_w - top_w) * t) / 2
        center = cx
        spread = belt_half * (0.62 if not overload and not spill else .95)
        x = int(rng.normal(center, max(4, spread * .42)))
        radius = int(rng.uniform(3, 9) * (1.15 if overload else 1.0))
        if abs(x - center) > belt_half - radius:
            x = int(center + np.sign(x - center) * (belt_half - radius - 2))
        shade = int(rng.integers(65, 145))
        cv2.circle(image, (x, y), radius, (shade, shade - 5, shade - 12), -1)

    labels = [{"class": "material", "bbox": [int(cx - bottom_w * (.46 if overload or spill else .33)), 0, int(cx + bottom_w * (.46 if overload or spill else .33)), height], "status": "overload" if overload else "normal"}]
    if spill:
        # Material outside the right edge, increasing toward the discharge end.
        spill_points = []
        for _ in range(26):
            y = int(rng.uniform(height * .55, height - 4))
            t = y / height
            belt_half = (top_w + (bottom_w - top_w) * t) / 2
            x = int(cx + belt_half + rng.uniform(4, width * .10))
            radius = int(rng.uniform(2, 7))
            cv2.circle(image, (min(width - 3, x), y), radius, (94, 83, 66), -1)
            spill_points.append((x, y))
        if spill_points:
            xs, ys = zip(*spill_points)
            labels.append({"class": "material_spill", "bbox": [max(0, min(xs) - 8), max(0, min(ys) - 8), min(width, max(xs) + 8), min(height, max(ys) + 8)], "status": "warning"})

    if scenario == "tear":
        tear_y = int(height * (.45 + .04 * math.sin(frame / fps)))
        tear_w = int(width * .08)
        tear = np.array([[int(cx - tear_w), tear_y], [int(cx - tear_w // 2), tear_y - 11], [int(cx + tear_w // 3), tear_y + 7], [int(cx + tear_w), tear_y - 13], [int(cx + tear_w // 2), tear_y + 18], [int(cx - tear_w // 3), tear_y + 9]], np.int32)
        cv2.fillPoly(image, [tear], (18, 20, 22))
        cv2.polylines(image, [tear], True, (40, 40, 42), 2)
        labels.append({"class": "tear", "bbox": [int(cx - tear_w - 4), tear_y - 20, int(cx + tear_w + 4), tear_y + 25], "status": "critical"})

    # Vision overlays are not baked into labels; they make the preview useful.
    cv2.line(image, (int(cx), 0), (int(cx), height), (235, 235, 220), 1, cv2.LINE_AA)
    left_top, right_top = int(cx - top_w * .42), int(cx + top_w * .42)
    left_bottom, right_bottom = int(cx - bottom_w * .42), int(cx + bottom_w * .42)
    cv2.line(image, (left_top, 0), (left_bottom, height), (80, 235, 155), 2)
    cv2.line(image, (right_top, 0), (right_bottom, height), (80, 235, 155), 2)

    labels.append({"class": "alignment", "offset_px": round(float(cx - width / 2), 2), "status": "warning" if abs(cx - width / 2) > width * .08 else "normal"})
    return image, labels


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="dataset/conveyor", help="Output directory")
    parser.add_argument("--scenario", choices=["normal", "overload", "tear", "material_spill"], default="normal")
    parser.add_argument("--seconds", type=float, default=10)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    video_path = out / f"conveyor_{args.scenario}.mp4"
    labels_path = out / f"conveyor_{args.scenario}.jsonl"
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (args.width, args.height))
    if not writer.isOpened():
        raise RuntimeError("Could not open MP4 writer; install an ffmpeg-enabled OpenCV build")
    with labels_path.open("w", encoding="utf-8") as labels_file:
        for frame_no in range(max(1, round(args.seconds * args.fps))):
            frame, labels = render_frame(args.width, args.height, frame_no, args.fps, args.scenario, args.seed)
            writer.write(frame)
            labels_file.write(json.dumps({"frame": frame_no, "fps": args.fps, "scenario": args.scenario, "labels": labels}) + "\n")
    writer.release()
    print(json.dumps({"video": str(video_path), "labels": str(labels_path), "frames": max(1, round(args.seconds * args.fps)), "scenario": args.scenario}, indent=2))


if __name__ == "__main__":
    main()

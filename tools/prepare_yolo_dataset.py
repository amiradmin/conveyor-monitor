#!/usr/bin/env python3
"""Convert generator MP4/JSONL pairs into a YOLO detection dataset."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import cv2

CLASS_NAMES = ["material", "overload_material", "tear", "material_spill"]


def write_label(path: Path, labels: list[dict], width: int, height: int) -> None:
    rows = []
    for label in labels:
        bbox = label.get("bbox")
        if not bbox:
            continue
        x1, y1, x2, y2 = bbox
        cls_name = "overload_material" if label["class"] == "material" and label.get("status") == "overload" else label["class"]
        if cls_name not in CLASS_NAMES:
            continue
        x1, x2 = max(0, min(width - 1, x1)), max(0, min(width - 1, x2))
        y1, y2 = max(0, min(height - 1, y1)), max(0, min(height - 1, y2))
        if x2 <= x1 or y2 <= y1:
            continue
        cx, cy = ((x1 + x2) / 2 / width, (y1 + y2) / 2 / height)
        bw, bh = ((x2 - x1) / width, (y2 - y1) / height)
        rows.append(f"{CLASS_NAMES.index(cls_name)} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
    path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")


def convert_pair(video_path: Path, labels_path: Path, out: Path, val_every: int) -> tuple[int, int]:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open {video_path}")
    labels_by_frame = {row["frame"]: row["labels"] for row in map(json.loads, labels_path.open(encoding="utf-8"))}
    written = {"train": 0, "val": 0}
    frame_no = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        split = "val" if frame_no % val_every == 0 else "train"
        stem = f"{video_path.stem}_{frame_no:06d}"
        image_path = out / "images" / split / f"{stem}.jpg"
        label_path = out / "labels" / split / f"{stem}.txt"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        label_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(image_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        write_label(label_path, labels_by_frame.get(frame_no, []), frame.shape[1], frame.shape[0])
        written[split] += 1
        frame_no += 1
    capture.release()
    return written["train"], written["val"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="dataset/conveyor")
    parser.add_argument("--output", default="dataset/yolo")
    parser.add_argument("--val-every", type=int, default=5, help="Put every Nth frame in validation")
    args = parser.parse_args()
    source, out = Path(args.input), Path(args.output)
    if out.exists():
        shutil.rmtree(out)
    total_train = total_val = 0
    for video in sorted(source.glob("conveyor_*.mp4")):
        labels = video.with_suffix(".jsonl")
        if not labels.exists():
            print(f"skip {video.name}: missing {labels.name}")
            continue
        train, val = convert_pair(video, labels, out, max(2, args.val_every))
        total_train += train
        total_val += val
    (out / "data.yaml").write_text("path: .\ntrain: images/train\nval: images/val\nnames:\n" + "\n".join(f"  {i}: {name}" for i, name in enumerate(CLASS_NAMES)) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "train_images": total_train, "val_images": total_val, "classes": CLASS_NAMES}, indent=2))


if __name__ == "__main__":
    main()

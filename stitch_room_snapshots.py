"""
Stitch saved camera snapshots into a simple visual room scan.

First run vision_camera_test.py and press s several times while slowly turning.
Or run guided_room_scan.py and follow its prompts.
Then run:
    python stitch_room_snapshots.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


SNAPSHOT_DIR = Path("vision_snapshots")
GUIDED_DIR = Path("guided_room_scan")
OUTPUT_DIR = Path("room_model")
OUTPUT_PATH = OUTPUT_DIR / "room_panorama.jpg"
CONTACT_SHEET_PATH = OUTPUT_DIR / "room_contact_sheet.jpg"


def load_snapshots(folder: Path) -> list[np.ndarray]:
    paths = sorted(folder.glob("*.jpg"))
    images = []

    for path in paths:
        image = read_image(path)
        if image is not None:
            images.append(image)

    if len(images) < 2:
        raise RuntimeError(
            f"Need at least 2 snapshots in {folder}. Run guided_room_scan.py and "
            "capture several overlapping photos."
        )

    return images


def read_image(path: Path) -> np.ndarray | None:
    data = np.fromfile(path, dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def write_image(path: Path, image: np.ndarray) -> bool:
    ext = path.suffix or ".jpg"
    ok, encoded = cv2.imencode(ext, image)
    if not ok:
        return False
    encoded.tofile(path)
    return True


def make_contact_sheet(images: list[np.ndarray]) -> np.ndarray:
    thumbs = []
    thumb_width = 240

    for image in images:
        scale = thumb_width / image.shape[1]
        thumb_height = int(image.shape[0] * scale)
        thumbs.append(cv2.resize(image, (thumb_width, thumb_height)))

    max_height = max(thumb.shape[0] for thumb in thumbs)
    padded = []

    for thumb in thumbs:
        bottom = max_height - thumb.shape[0]
        padded.append(cv2.copyMakeBorder(thumb, 0, bottom, 0, 0, cv2.BORDER_CONSTANT))

    return np.hstack(padded)


def stitch_images(images: list[np.ndarray]) -> tuple[bool, np.ndarray]:
    stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
    status, panorama = stitcher.stitch(images)
    return status == cv2.Stitcher_OK, panorama


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stitch room scan snapshots.")
    parser.add_argument(
        "--folder",
        type=Path,
        default=None,
        help="Folder of jpg snapshots. Defaults to guided_room_scan if it has images.",
    )
    return parser.parse_args()


def choose_folder(folder: Path | None) -> Path:
    if folder is not None:
        return folder
    if list(GUIDED_DIR.glob("*.jpg")):
        return GUIDED_DIR
    return SNAPSHOT_DIR


def main() -> None:
    args = parse_args()
    source_folder = choose_folder(args.folder)
    OUTPUT_DIR.mkdir(exist_ok=True)
    images = load_snapshots(source_folder)

    contact_sheet = make_contact_sheet(images)
    write_image(CONTACT_SHEET_PATH, contact_sheet)

    stitched, panorama = stitch_images(images)
    if stitched:
        write_image(OUTPUT_PATH, panorama)
        print(f"Saved stitched room scan: {OUTPUT_PATH}")
    else:
        print("Could not stitch a panorama from these snapshots.")
        print("Saved a side-by-side contact sheet instead.")

    print(f"Source folder: {source_folder}")
    print(f"Saved contact sheet: {CONTACT_SHEET_PATH}")


if __name__ == "__main__":
    main()

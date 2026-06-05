"""
Guided camera capture for making a visual room scan.

Run:
    python guided_room_scan.py

Controls:
    space  capture when the guide says READY
    a      toggle automatic capture
    q      finish and save
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
OUTPUT_DIR = Path("guided_room_scan")

# These values are tuned for a slow left-to-right room scan.
MIN_SHIFT_RATIO = 0.14
MAX_SHIFT_RATIO = 0.42
MIN_GOOD_MATCHES = 25


def open_camera() -> cv2.VideoCapture:
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera = cv2.VideoCapture(CAMERA_INDEX)

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, 15)

    if not camera.isOpened():
        raise RuntimeError(
            "Could not open the laptop camera. Make sure no other app is using it."
        )

    return camera


def read_frame(camera: cv2.VideoCapture):
    for _ in range(10):
        ok, frame = camera.read()
        if ok:
            return frame
    raise RuntimeError("Could not read a frame from the camera.")


def frame_motion(previous: np.ndarray, current: np.ndarray) -> tuple[float, int]:
    orb = cv2.ORB_create(nfeatures=900)
    prev_gray = cv2.cvtColor(previous, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)

    prev_points, prev_desc = orb.detectAndCompute(prev_gray, None)
    curr_points, curr_desc = orb.detectAndCompute(curr_gray, None)

    if prev_desc is None or curr_desc is None:
        return 0.0, 0

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = sorted(matcher.match(prev_desc, curr_desc), key=lambda m: m.distance)
    good_matches = matches[:80]

    if len(good_matches) < 8:
        return 0.0, len(good_matches)

    shifts = []
    for match in good_matches:
        prev_x = prev_points[match.queryIdx].pt[0]
        curr_x = curr_points[match.trainIdx].pt[0]
        shifts.append(prev_x - curr_x)

    median_shift = float(np.median(shifts))
    return median_shift / current.shape[1], len(good_matches)


def guide_text(shift_ratio: float, matches: int, capture_count: int) -> tuple[str, tuple[int, int, int]]:
    if capture_count == 0:
        return "Point at the left side of the room, then press SPACE", (0, 220, 255)

    if matches < MIN_GOOD_MATCHES:
        return "Move slower or point at textured objects", (0, 180, 255)

    if shift_ratio < MIN_SHIFT_RATIO:
        return "Turn RIGHT slowly", (255, 255, 255)

    if shift_ratio > MAX_SHIFT_RATIO:
        return "Too far, turn LEFT a little", (0, 120, 255)

    return "READY - press SPACE", (80, 255, 80)


def draw_overlay(frame, message: str, color, shift_ratio: float, matches: int, auto_capture: bool) -> None:
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 94), (0, 0, 0), -1)
    cv2.putText(
        frame,
        message,
        (16, 34),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.82,
        color,
        2,
        cv2.LINE_AA,
    )
    details = (
        f"shift {shift_ratio:.2f} | matches {matches} | "
        f"auto {'on' if auto_capture else 'off'} | SPACE capture | A auto | Q finish"
    )
    cv2.putText(
        frame,
        details,
        (16, 72),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (220, 220, 220),
        1,
        cv2.LINE_AA,
    )


def save_capture(frame, capture_count: int) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"scan_{capture_count:02d}_{stamp}.jpg"
    cv2.imwrite(str(path), frame)
    print(f"Saved {path}")
    return path


def main() -> None:
    camera = open_camera()
    previous_capture = None
    capture_count = 0
    auto_capture = False
    ready_frames = 0

    print("Start at the left side of the room. Press SPACE to take the first photo.")

    try:
        while True:
            frame = read_frame(camera)
            shift_ratio = 0.0
            matches = 0

            if previous_capture is not None:
                shift_ratio, matches = frame_motion(previous_capture, frame)

            message, color = guide_text(shift_ratio, matches, capture_count)
            ready = message.startswith("READY")

            if ready:
                ready_frames += 1
            else:
                ready_frames = 0

            display = frame.copy()
            draw_overlay(display, message, color, shift_ratio, matches, auto_capture)
            cv2.imshow("Guided Room Scan", display)

            key = cv2.waitKey(1) & 0xFF
            should_capture = key == ord(" ")

            if auto_capture and ready_frames > 12:
                should_capture = True
                ready_frames = 0

            if key == ord("q"):
                break
            if key == ord("a"):
                auto_capture = not auto_capture
            if should_capture:
                capture_count += 1
                save_capture(frame, capture_count)
                previous_capture = frame.copy()

        print(f"Finished with {capture_count} saved photos in {OUTPUT_DIR}.")
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

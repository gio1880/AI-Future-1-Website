"""
Laptop webcam vision test for the AI Future innovation project.

Run:
    python vision_camera_test.py
    python vision_camera_test.py --check

Controls:
    e  toggle edge detection
    s  save the current frame and edge image
    q  quit
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import cv2


CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
OUTPUT_DIR = Path("vision_snapshots")


def open_camera(camera_index: int) -> cv2.VideoCapture:
    camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera = cv2.VideoCapture(camera_index)

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, 15)

    if not camera.isOpened():
        raise RuntimeError(
            "Could not open the laptop camera. Make sure no other app is using it."
        )

    return camera


def detect_edges(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 60, 140)
    return edges


def draw_status(frame, show_edges: bool) -> None:
    mode = "edges" if show_edges else "camera"
    text = f"Mode: {mode} | e: edges | s: save | q: quit"
    cv2.rectangle(frame, (8, 8), (470, 42), (0, 0, 0), -1)
    cv2.putText(
        frame,
        text,
        (16, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def save_snapshot(frame, edges) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    frame_path = OUTPUT_DIR / f"camera_{stamp}.jpg"
    edge_path = OUTPUT_DIR / f"edges_{stamp}.jpg"

    cv2.imwrite(str(frame_path), frame)
    cv2.imwrite(str(edge_path), edges)
    print(f"Saved {frame_path} and {edge_path}")


def read_frame(camera: cv2.VideoCapture):
    for _ in range(10):
        ok, frame = camera.read()
        if ok:
            return frame
    raise RuntimeError("Could not read a frame from the camera.")


def run_one_frame_check(camera_index: int) -> None:
    camera = open_camera(camera_index)
    try:
        frame = read_frame(camera)
        edges = detect_edges(frame)
        save_snapshot(frame, edges)
        print("Camera check passed.")
    finally:
        camera.release()


def run_live_view(camera_index: int) -> None:
    camera = open_camera(camera_index)
    show_edges = False

    print("Camera started. Press e for edges, s to save, q to quit.")

    try:
        while True:
            frame = read_frame(camera)

            edges = detect_edges(frame)

            if show_edges:
                display = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            else:
                display = frame.copy()

            draw_status(display, show_edges)
            cv2.imshow("AI Future Laptop Camera Test", display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("e"):
                show_edges = not show_edges
            if key == ord("s"):
                save_snapshot(frame, edges)
    finally:
        camera.release()
        cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Laptop webcam vision test.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Capture one frame, save output images, and exit.",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=CAMERA_INDEX,
        help="Camera index to use. Try 1 if 0 does not work.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check:
        run_one_frame_check(args.camera)
    else:
        run_live_view(args.camera)


if __name__ == "__main__":
    main()

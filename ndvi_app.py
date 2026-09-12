"""Interactive NDVI viewer.

Usage:
    python ndvi_app.py path/to/image.jpg
"""

from __future__ import annotations

import argparse

import cv2

from ndvi_processor import load_image, process_image, roi_mean


WINDOW_NAME = "NDVI viewer"


class RoiSelector:
    def __init__(self, display: object, ndvi: object) -> None:
        self.display = display
        self.ndvi = ndvi
        self.start: tuple[int, int] | None = None
        self.current: tuple[int, int] | None = None

    def handle_mouse(self, event: int, x: int, y: int, _flags: int, _data: object) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            self.start = (x, y)
            self.current = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self.start is not None:
            self.current = (x, y)
            self._render()
        elif event == cv2.EVENT_LBUTTONUP and self.start is not None:
            self.current = (x, y)
            self._render()
            self._print_score()

    def _render(self) -> None:
        frame = self.display.copy()
        if self.start is not None and self.current is not None:
            cv2.rectangle(frame, self.start, self.current, (0, 0, 0), 2)
        cv2.imshow(WINDOW_NAME, frame)

    def _print_score(self) -> None:
        if self.start is None or self.current is None:
            return
        score = roi_mean(
            self.ndvi,
            self.start[0],
            self.start[1],
            self.current[0],
            self.current[1],
        )
        print(f"Mean NDVI: {score:.3f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="View an NDVI image and measure rectangular regions.")
    parser.add_argument("image", help="Path to an image file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = process_image(load_image(args.image))
    selector = RoiSelector(result.display, result.ndvi)

    cv2.namedWindow(WINDOW_NAME)
    cv2.imshow(WINDOW_NAME, result.display)
    cv2.setMouseCallback(WINDOW_NAME, selector.handle_mouse)
    print("Drag to select a region. Press Esc or q to quit.")

    while True:
        key = cv2.waitKey(20) & 0xFF
        if key in (27, ord("q")):
            break
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
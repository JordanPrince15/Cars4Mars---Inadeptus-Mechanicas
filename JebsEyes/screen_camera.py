import cv2
import numpy as np
from mss import mss


class ScreenCamera:
    """
    Capture the desktop (or a chosen monitor) as a camera source.

    Used when the FPV feed is already being shown on screen.
    """

    def __init__(self, monitor=1, max_width=1280):
        self.max_width = max_width
        self.sct = mss()
        self.set_monitor(monitor)

        print("✓ Screen capture selected.")
        print(f"  Monitor: {self.monitor_index}")
        print(
            f"  Region: {self.monitor['width']}x{self.monitor['height']} "
            f"at ({self.monitor['left']}, {self.monitor['top']})"
        )

    def list_monitors(self):
        monitors = []

        for index, monitor in enumerate(self.sct.monitors):
            monitors.append({
                "id": index,
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"],
                "label": (
                    "All monitors"
                    if index == 0
                    else f"Monitor {index}"
                )
            })

        return monitors

    def set_monitor(self, monitor_index):
        monitors = self.sct.monitors

        if monitor_index < 0 or monitor_index >= len(monitors):
            monitor_index = 1 if len(monitors) > 1 else 0

        self.monitor_index = monitor_index
        self.monitor = monitors[monitor_index]

    def read(self):
        shot = self.sct.grab(self.monitor)
        frame = np.asarray(shot)

        if frame.size == 0:
            return False, None

        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        if (
            self.max_width
            and frame.shape[1] > self.max_width
        ):
            scale = self.max_width / frame.shape[1]
            frame = cv2.resize(
                frame,
                (
                    self.max_width,
                    int(frame.shape[0] * scale)
                )
            )

        return True, frame

    def release(self):
        try:
            self.sct.close()
        except Exception:
            pass

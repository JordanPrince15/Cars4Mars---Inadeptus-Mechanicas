import cv2
import time
from pathlib import Path

from JebsEyes.mission_controller import MissionController
from JebsEyes.network_camera import NetworkCamera
from JebsEyes.screen_camera import ScreenCamera


# ============================================================
# CAMERA CONFIGURATION
# ============================================================

# Choose the camera mode here.
# How to run: python -m JebsEyes.ui.main_ui
# "auto"    -> Try network camera first, then laptop webcam
# "network" -> Raspberry Pi network camera
# "webcam"  -> Laptop webcam
# "screen"  -> Capture the FPV feed from the desktop
# "off"     -> No camera
#
CAMERA_MODE = "screen"


# Which monitor to capture. 1 is the primary display.
# 0 captures every monitor as one image.
SCREEN_MONITOR = 1

# Downscale wide desktops so YOLO stays usable.
SCREEN_MAX_WIDTH = 1280

# Annotated screenshots are written here.
CAPTURE_DIR = Path(__file__).resolve().parents[1] / "captures"


# Raspberry Pi camera stream
NETWORK_STREAM_URL = "http://192.168.0.142:5000/video"


# Laptop webcam settings
WEBCAM_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480


# ============================================================
# CAMERA MANAGER
# ============================================================

class CameraManager:

    def __init__(self, mode=CAMERA_MODE):

        self.mode = mode
        self.camera = None
        self.active_mode = None

        self.connect()


    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    def connect(self):

        self.release()

        # ================================================
        # OFF / SIMULATION
        # ================================================

        if self.mode == "off":

            print("Camera disabled.")

            self.active_mode = "off"
            return


        # ================================================
        # NETWORK CAMERA
        # ================================================

        if self.mode == "network":

            print("Connecting to Raspberry Pi camera...")

            try:

                self.camera = NetworkCamera(
                    stream_url=NETWORK_STREAM_URL
                )

                self.active_mode = "network"

                print("✓ Network camera selected.")

            except Exception as e:

                print(f"✗ Network camera failed: {e}")

                self.camera = None
                self.active_mode = None

            return


        # ================================================
        # SCREEN CAPTURE (FPV)
        # ================================================

        if self.mode == "screen":

            print("Capturing desktop / FPV screen...")

            try:

                self.camera = ScreenCamera(
                    monitor=SCREEN_MONITOR,
                    max_width=SCREEN_MAX_WIDTH
                )

                ret, frame = self.camera.read()

                if not ret or frame is None:

                    print("✗ Screen capture produced no frame.")

                    self.camera.release()

                    self.camera = None
                    self.active_mode = None

                    return

                self.active_mode = "screen"

                print("✓ Screen capture selected.")

            except Exception as e:

                print(f"✗ Screen capture failed: {e}")

                self.camera = None
                self.active_mode = None

            return


        # ================================================
        # LAPTOP WEBCAM
        # ================================================

        if self.mode == "webcam":

            print("Opening laptop webcam...")

            cap = cv2.VideoCapture(WEBCAM_INDEX)

            if not cap.isOpened():

                print("✗ Could not open laptop webcam.")

                cap.release()

                self.camera = None
                self.active_mode = None

                return

            cap.set(
                cv2.CAP_PROP_FRAME_WIDTH,
                FRAME_WIDTH
            )

            cap.set(
                cv2.CAP_PROP_FRAME_HEIGHT,
                FRAME_HEIGHT
            )

            # Make sure the camera actually produces a frame
            ret, frame = cap.read()

            if not ret or frame is None:

                print("✗ Laptop webcam opened but produced no frame.")

                cap.release()

                self.camera = None
                self.active_mode = None

                return

            self.camera = cap
            self.active_mode = "webcam"

            print("✓ Laptop webcam selected.")

            return


        # ================================================
        # AUTO MODE
        # ================================================

        if self.mode == "auto":

            print("Searching for available cameras...")

            # ------------------------------------------------
            # First try Raspberry Pi
            # ------------------------------------------------

            print("Checking Raspberry Pi camera...")

            try:

                network_camera = NetworkCamera(
                    stream_url=NETWORK_STREAM_URL
                )

                # Test whether the stream actually works
                ret, frame = network_camera.read()

                if ret and frame is not None:

                    self.camera = network_camera
                    self.active_mode = "network"

                    print("✓ Raspberry Pi camera found.")

                    return

                network_camera.release()

            except Exception as e:

                print(f"  Raspberry Pi camera unavailable.")

            # ------------------------------------------------
            # If Pi isn't available, try laptop webcam
            # ------------------------------------------------

            print("Checking laptop webcam...")

            cap = cv2.VideoCapture(WEBCAM_INDEX)

            if cap.isOpened():

                cap.set(
                    cv2.CAP_PROP_FRAME_WIDTH,
                    FRAME_WIDTH
                )

                cap.set(
                    cv2.CAP_PROP_FRAME_HEIGHT,
                    FRAME_HEIGHT
                )

                ret, frame = cap.read()

                if ret and frame is not None:

                    self.camera = cap
                    self.active_mode = "webcam"

                    print("✓ Laptop webcam found.")

                    return

            cap.release()

            # ------------------------------------------------
            # Nothing found
            # ------------------------------------------------

            print("✗ No camera found.")

            self.camera = None
            self.active_mode = None

            return


        # ====================================================
        # INVALID MODE
        # ====================================================

        raise ValueError(
            f"Unknown CAMERA_MODE: {self.mode}"
        )


    # --------------------------------------------------------
    # READ FRAME
    # --------------------------------------------------------

    def read(self):

        if self.camera is None:

            raise ConnectionError(
                "No camera is currently connected."
            )


        # ----------------------------------------------------
        # Network camera
        # ----------------------------------------------------

        if self.active_mode == "network":

            return self.camera.read()


        # ----------------------------------------------------
        # Screen capture
        # ----------------------------------------------------

        if self.active_mode == "screen":

            ret, frame = self.camera.read()

            if not ret or frame is None:

                raise ConnectionError(
                    "Screen capture failed."
                )

            return frame, None


        if self.active_mode == "webcam":

            ret, frame = self.camera.read()

            if not ret or frame is None:

                raise ConnectionError(
                    "Laptop webcam disconnected."
                )

            # Flip webcam image
            # frame = cv2.flip(frame, -1)

            return frame, None


        raise ConnectionError(
            "Camera is not active."
        )


    # --------------------------------------------------------
    # TOGGLE CAMERA
    # --------------------------------------------------------

    def toggle(self):

        if self.mode == "network":

            self.mode = "webcam"

        else:

            self.mode = "network"


        print()
        print("==============================")
        print(
            f"Switching to {self.mode.upper()} camera"
        )
        print("==============================")


        self.connect()


    # --------------------------------------------------------
    # RELEASE
    # --------------------------------------------------------

    def release(self):

        if self.camera is None:
            return

        try:

            self.camera.release()

        except Exception:

            pass

        self.camera = None
        self.active_mode = None


# ============================================================
# VISION LOOP
# ============================================================

def _draw_balloon_overlays(frame, detections):
    for detection in detections:
        x = detection["x"]
        y = detection["y"]
        width = detection["width"]
        height = detection["height"]

        x1 = max(0, int(x - width / 2))
        y1 = max(0, int(y - height / 2))
        x2 = min(frame.shape[1] - 1, int(x + width / 2))
        y2 = min(frame.shape[0] - 1, int(y + height / 2))

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            3
        )

        label = (
            detection["class"].replace("_", " ").upper()
            + f" {detection['confidence']:.0%}"
        )

        cv2.putText(
            frame,
            label,
            (x1, max(30, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2
        )


def vision_loop(state, stop_event, camera, mission_controller, frame_broker=None):
    print()
    print("==============================")
    print("       JEB VISION THREAD")
    print("==============================")


    # ========================================================
    # MAIN LOOP
    # ========================================================

    while not stop_event.is_set():

        # ----------------------------------------------------
        # Get frame
        # ----------------------------------------------------

        try:
            frame, distance = camera.read()

        except Exception as e:
            print(f"⚠ Camera error: {e}")
            time.sleep(2)

            try:
                print("Attempting camera reconnect...")
                camera.connect()

            except Exception:
                pass

            continue

        with state.lock:
            detecting = getattr(state, "detection_enabled", True)

        # Keep a copy without detection overlays for venue training.
        raw_frame = frame.copy()

        # Train mode skips YOLO / balloon inference so the
        # camera is only used for grab-live snapshots.
        if not detecting:
            with state.lock:
                state.frame = raw_frame.copy()
                state.raw_frame = raw_frame
                state.distance_cm = distance
                state.ball_detected = False
                state.object_class = None
                state.object_direction = None
                state.balloon_detected = False
                state.balloon_class = None
                state.balloon_detections = []

            time.sleep(0.2)
            continue

        # ----------------------------------------------------
        # Process frame through MissionController
        # ----------------------------------------------------

        result = mission_controller.process_frame(frame)

        # ----------------------------------------------------
        # Get object-mission result
        # ----------------------------------------------------

        ball = result.get("ball")
        direction = result.get("direction")
        hammers = result.get("hammers", [])
        balloon_detections = result.get("detections", [])

        if balloon_detections:
            _draw_balloon_overlays(frame, balloon_detections)

        if frame_broker is not None:
            frame_broker.publish(frame)

        # ====================================================
        # WRITE TO SHARED ROBOT STATE
        # ====================================================

        with state.lock:

            # ------------------------------------------------
            # Camera frame
            # ------------------------------------------------

            state.frame = frame.copy()
            state.raw_frame = raw_frame

            # ------------------------------------------------
            # Distance
            # ------------------------------------------------

            state.distance_cm = distance

            # ------------------------------------------------
            # Tennis ball
            # ------------------------------------------------
        

            if ball:

                state.ball_detected = True
                state.ball_x = ball["x"]
                state.ball_y = ball["y"]

                state.ball_confidence = (ball["confidence"])

                state.object_class = "tennis_ball"
                state.object_direction = direction

            else:

                state.ball_detected = False
                state.object_class = None
                state.object_direction = None

            # =================================================
            # BALLOONS
            # =================================================

            state.balloon_detections = balloon_detections

            if balloon_detections:

                best = max(
                    balloon_detections,
                    key=lambda d: d["confidence"]
                )

                state.balloon_detected = True
                state.balloon_class = best["class"]
                state.balloon_x = best["x"]
                state.balloon_y = best["y"]
                state.balloon_width = best["width"]
                state.balloon_height = best["height"]
                state.balloon_confidence = best["confidence"]

            else:

                state.balloon_detected = False
                state.balloon_class = None
                state.balloon_x = 0
                state.balloon_y = 0
                state.balloon_width = 0
                state.balloon_height = 0
                state.balloon_confidence = 0.0

        # ----------------------------------------------------
        # Small delay
        # ----------------------------------------------------

        time.sleep(0.005)

    # ========================================================
    # SHUTDOWN
    # ========================================================

    camera.release()

    print()
    print("==============================")
    print("    JEB VISION THREAD STOPPED")
    print("==============================")
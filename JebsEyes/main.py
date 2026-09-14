import cv2
import time

from JebsEyes.mission_controller import MissionController
from JebsEyes.network_camera import NetworkCamera


# ============================================================
# CAMERA CONFIGURATION
# ============================================================

# Choose the camera mode here.
# How to run: python -m JebsEyes.ui.main_ui
# "auto"    -> Try network camera first, then laptop webcam
# "network" -> Raspberry Pi network camera

# "webcam"  -> Laptop webcam
# "off"     -> No camera
#
CAMERA_MODE = "webcam"  # Change this to "network" for Raspberry Pi camera, "webcam" for laptop webcam, or "off" to disable camera


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
        # Laptop webcam
        # ----------------------------------------------------

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

def vision_loop(state, stop_event, camera, mission_controller):
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

        # ----------------------------------------------------
        # Process frame through MissionController
        # ----------------------------------------------------

        result = mission_controller.process_frame(frame)

        # ----------------------------------------------------
        # Get object-mission result
        # ----------------------------------------------------

        ball = result.get("ball")
        direction = result.get("direction")
        balloon_detections = result.get("detections", [])

        # ====================================================
        # WRITE TO SHARED ROBOT STATE
        # ====================================================

        with state.lock:

            # ------------------------------------------------
            # Camera frame
            # ------------------------------------------------

            state.frame = frame.copy()

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
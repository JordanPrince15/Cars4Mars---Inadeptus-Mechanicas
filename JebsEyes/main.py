import cv2
import time

from JebsEyes.network_camera import NetworkCamera
from JebsEyes.hsv_ball import detect_tennis_ball_via_colour
from JebsEyes.yolo_ball import TennisBallDetector
from JebsEyes.fusion import fuse_detections
from JebsEyes.balloon_decector import BalloonDetector


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
CAMERA_MODE = "auto"


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

def vision_loop(state, stop_event, camera):

    print()
    print("==============================")
    print("       JEB VISION THREAD")
    print("==============================")


    detector = TennisBallDetector()

    balloon_detector = BalloonDetector()

    frame_counter = 0

    last_yolo = None


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
        # HSV detection
        # ----------------------------------------------------

        hsv_ball = detect_tennis_ball_via_colour(frame)


        # ----------------------------------------------------
        # YOLO detection
        #
        # Run every 5 frames instead of every frame to
        # reduce CPU usage.
        # ----------------------------------------------------

        frame_counter += 1


        if frame_counter % 30 == 0:

            balloon_result = balloon_detector.detect(frame)
            ball_result = detector.detect(frame)

            print()
            print("===============ROBOFLOW===============")
            print(balloon_result)
            print("======================================")
            print()

            if balloon_result is not None:
                print(f"Balloon detection result: {balloon_result}")

            if ball_result is not None:
                print(f"Ball detection result: {ball_result}")

            small = cv2.resize(
                frame,
                (320, 240)
            )


            yolo = detector.detect(small)


            if yolo:

                scale_x = frame.shape[1] / 320
                scale_y = frame.shape[0] / 240


                last_yolo = {

                    "x": int(
                        yolo["x"] * scale_x
                    ),

                    "y": int(
                        yolo["y"] * scale_y
                    ),

                    "size": int(
                        yolo["size"]
                        * (scale_x + scale_y)
                        / 2
                    ),

                    "confidence":
                        yolo["confidence"]
                }


            else:

                last_yolo = None


        # ----------------------------------------------------
        # Fuse HSV + YOLO
        # ----------------------------------------------------

        ball = fuse_detections(
            hsv_ball,
            last_yolo
        )


        # ----------------------------------------------------
        # Write to shared robot state
        # ----------------------------------------------------

        with state.lock:

            state.frame = frame.copy()


            if ball:

                state.ball_detected = True

                state.ball_x = ball["x"]

                state.ball_y = ball["y"]

                state.ball_confidence = (
                    ball["confidence"]
                )


            else:

                state.ball_detected = False


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
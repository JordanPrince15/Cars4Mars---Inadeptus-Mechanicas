import tkinter as tk
from PIL import Image, ImageTk
import cv2
import threading
import serial
import time

from JebsEyes.robot_state import RobotState
from JebsEyes.network_camera import NetworkCamera
from JebsEyes.hsv_ball import detect_tennis_ball_via_colour
from JebsEyes.yolo_ball import TennisBallDetector
from JebsEyes.fusion import fuse_detections
from JebsEyes.ui.panda_panel import PandaApp


# =========================================================
# VISION LOOP
# =========================================================

def vision_loop(state, stop_event):

    print("================================")
    print("       JEB VISION THREAD")
    print("================================")

    # -----------------------------------------------------
    # YOLO
    # -----------------------------------------------------

    print("Loading YOLO detector...")

    try:
        tennis_detector = TennisBallDetector()
        print("✅ YOLO detector ready")

    except Exception as e:
        print(f"❌ Failed to load YOLO detector: {e}")
        tennis_detector = None

    # -----------------------------------------------------
    # CAMERA
    # -----------------------------------------------------

    print()
    print("Connecting to Jeb's camera...")

    try:
        net_cam = NetworkCamera(
            stream_url="http://192.168.0.142:5000/video"
        )

        print("✅ Jeb's camera connected")

    except Exception as e:

        print(f"❌ Camera connection failed: {e}")

        net_cam = None

    # -----------------------------------------------------
    # YOLO SETTINGS
    # -----------------------------------------------------

    frame_count = 0

    YOLO_INTERVAL = 5

    last_yolo_ball = None

    # -----------------------------------------------------
    # MAIN VISION LOOP
    # -----------------------------------------------------

    while not stop_event.is_set():

        # =================================================
        # CAMERA CONNECTION
        # =================================================

        if net_cam is None:

            time.sleep(2)

            if stop_event.is_set():
                break

            try:

                print("Attempting to reconnect camera...")

                net_cam = NetworkCamera(
                    stream_url="http://192.168.0.142:5000/video"
                )

                print("✅ Camera reconnected")

            except Exception as e:

                print(
                    f"⚠️ Camera reconnect failed: {e}"
                )

                continue

        # =================================================
        # READ CAMERA
        # =================================================

        try:

            frame, distance = net_cam.read()

            if frame is None:
                continue

        except Exception as e:

            print(
                f"⚠️ Camera read error: {e}"
            )

            try:
                net_cam.release()
            except Exception:
                pass

            net_cam = None

            continue

        # =================================================
        # HSV DETECTION
        # =================================================

        try:

            hsv_ball = detect_tennis_ball_via_colour(
                frame
            )

        except Exception as e:

            print(
                f"⚠️ HSV detection error: {e}"
            )

            hsv_ball = None

        # =================================================
        # YOLO DETECTION
        # =================================================

        frame_count += 1

        if (
            tennis_detector is not None
            and frame_count % YOLO_INTERVAL == 0
        ):

            try:

                # Reduce image size before YOLO
                small = cv2.resize(
                    frame,
                    (320, 240)
                )

                yolo_ball = tennis_detector.detect(
                    small
                )

                if yolo_ball:

                    scale_x = (
                        frame.shape[1] / 320
                    )

                    scale_y = (
                        frame.shape[0] / 240
                    )

                    last_yolo_ball = {

                        "x": int(
                            yolo_ball["x"]
                            * scale_x
                        ),

                        "y": int(
                            yolo_ball["y"]
                            * scale_y
                        ),

                        "size": int(
                            yolo_ball["size"]
                            * (scale_x + scale_y)
                            / 2
                        ),

                        "confidence":
                            yolo_ball[
                                "confidence"
                            ],
                    }

                else:

                    last_yolo_ball = None

            except Exception as e:

                print(
                    f"⚠️ YOLO detection error: {e}"
                )

        # =================================================
        # FUSE HSV + YOLO
        # =================================================

        try:

            ball = fuse_detections(
                hsv_ball,
                last_yolo_ball
            )

        except Exception as e:

            print(
                f"⚠️ Fusion error: {e}"
            )

            ball = None

        # =================================================
        # WRITE TO SHARED ROBOT STATE
        # =================================================

        with state.lock:

            state.frame = (
                frame.copy()
                if frame is not None
                else None
            )

            if ball:

                state.ball_detected = True

                state.ball_x = ball["x"]

                state.ball_y = ball["y"]

                state.ball_confidence = (
                    ball["confidence"]
                )

            else:

                state.ball_detected = False

        # =================================================
        # SMALL DELAY
        # =================================================

        time.sleep(0.005)

    # =====================================================
    # CLEANUP
    # =====================================================

    if net_cam is not None:

        try:
            net_cam.release()

        except Exception:
            pass

    print("🛑 Vision thread stopped")


# =========================================================
# ROVER UI
# =========================================================

class RoverUI:

    def __init__(self, root):

        self.root = root

        # -------------------------------------------------
        # WINDOW
        # -------------------------------------------------

        self.root.title(
            "Rover Mission Control"
        )

        self.root.geometry(
            "1000x700"
        )

        self.root.configure(
            bg="lightgray"
        )

        # -------------------------------------------------
        # SHARED STATE
        # -------------------------------------------------

        self.state = RobotState()

        self.stop_event = (
            threading.Event()
        )

        # -------------------------------------------------
        # SERIAL / GROUND PICO
        # -------------------------------------------------

        self.pico = None

        try:

            self.pico = serial.Serial(
                "COM7",
                115200,
                timeout=1
            )

            print(
                "✅ Connected to Pico on COM7"
            )

        except Exception as e:

            print(
                f"⚠️ Failed to connect to Pico: {e}"
            )

            self.pico = None

        # -------------------------------------------------
        # CURRENT PAN
        # -------------------------------------------------

        self.current_pan = 90

        # -------------------------------------------------
        # START VISION THREAD
        # -------------------------------------------------

        self.vision_thread = (
            threading.Thread(
                target=vision_loop,
                args=(
                    self.state,
                    self.stop_event
                ),
                daemon=True
            )
        )

        self.vision_thread.start()

        # =================================================
        # LEFT PANEL
        # =================================================

        left_frame = tk.Frame(
            root,
            bg="white"
        )

        left_frame.pack(
            side="left",
            fill="both",
            expand=True
        )

        # -------------------------------------------------
        # VIDEO
        # -------------------------------------------------

        self.video_label = tk.Label(
            left_frame,
            bg="black"
        )

        self.video_label.pack(
            padx=20,
            pady=20
        )

        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------

        self.status = tk.Label(
            left_frame,
            text=(
                "WiFi: ● Connected | "
                "Battery: -- | "
                "Telemetry: OK"
            ),
            font=("Arial", 12),
            bg="white"
        )

        self.status.pack(
            pady=5
        )

        # =================================================
        # RIGHT PANEL
        # =================================================

        panda_frame = tk.Frame(
            root,
            width=400,
            bg="black"
        )

        panda_frame.pack(
            side="right",
            fill="y"
        )

        panda_frame.pack_propagate(
            False
        )

        # -------------------------------------------------
        # PANDA3D
        # -------------------------------------------------

        self.panda = PandaApp(
            panda_frame.winfo_id(),
            root
        )

        # -------------------------------------------------
        # UI UPDATE LOOP
        # -------------------------------------------------

        self.update_ui()

        # -------------------------------------------------
        # CLEAN SHUTDOWN
        # -------------------------------------------------

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

    # =====================================================
    # SEND COMMAND TO GROUND PICO
    # =====================================================

    def send_pico_command(self, command):

        if self.pico is not None:

            try:

                self.pico.write(
                    (command + "\n").encode()
                )

                self.pico.flush()

            except Exception as e:

                print(
                    f"❌ Pico connection lost: {e}"
                )

                try:
                    self.pico.close()
                except Exception:
                    pass

                self.pico = None

        else:

            print(
                f"[MOCK PICO] Action: {command}"
            )

    # =====================================================
    # UI UPDATE
    # =====================================================

    def update_ui(self):

        # -------------------------------------------------
        # READ SHARED STATE
        # -------------------------------------------------

        with self.state.lock:

            frame = self.state.frame

            detected_ball = (
                self.state.ball_detected
            )

            x = self.state.ball_x

            y = self.state.ball_y

            confidence = (
                self.state.ball_confidence
            )

        # =================================================
        # TARGET TRACKING
        # =================================================

        if detected_ball and frame is not None:

            # ---------------------------------------------
            # Find actual frame centre
            # ---------------------------------------------

            frame_center = (
                frame.shape[1] // 2
            )

            error = x - frame_center

            # ---------------------------------------------
            # Deadzone
            # ---------------------------------------------

            deadzone = 40

            # ---------------------------------------------
            # Move head LEFT
            # ---------------------------------------------

            if error < -deadzone:

                self.send_pico_command(
                    "LEFT"
                )

                self.current_pan -= 2

                self.current_pan = max(
                    60,
                    self.current_pan
                )

            # ---------------------------------------------
            # Move head RIGHT
            # ---------------------------------------------

            elif error > deadzone:

                self.send_pico_command(
                    "RIGHT"
                )

                self.current_pan += 2

                self.current_pan = min(
                    120,
                    self.current_pan
                )

        # =================================================
        # BUILD BALL DATA
        # =================================================

        ball = None

        if detected_ball:

            ball = {

                "x": x,

                "y": y,

                "size": 20,

                "confidence":
                    confidence
            }

        # =================================================
        # UPDATE PANDA3D
        # =================================================

        if detected_ball:

            # ---------------------------------------------
            # Convert camera coordinates to simulation
            # coordinates
            # ---------------------------------------------

            if frame is not None:

                frame_width = (
                    frame.shape[1]
                )

                frame_height = (
                    frame.shape[0]
                )

                px = (
                    x - frame_width / 2
                ) / 10

                py = (
                    y - frame_height / 2
                ) / 10

            else:

                px = 0
                py = 0

            # ---------------------------------------------
            # Update simulated ball
            # ---------------------------------------------

            self.panda.sim.set_ball_position(
                px,
                py,
                0.5
            )

            # ---------------------------------------------
            # Update sensor/head angle
            # ---------------------------------------------

            self.panda.sim.set_sensor_angle(
                self.current_pan
            )

        else:

            self.panda.sim.ball_node.hide()

        # =================================================
        # UPDATE VIDEO
        # =================================================

        if frame is not None:

            display = frame.copy()

            # ---------------------------------------------
            # Draw detected ball
            # ---------------------------------------------

            if ball:

                cv2.circle(
                    display,
                    (
                        ball["x"],
                        ball["y"]
                    ),
                    ball["size"],
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    display,
                    (
                        f"Tennis Ball "
                        f"{ball['confidence']:.2f}"
                    ),
                    (
                        max(
                            10,
                            ball["x"] - 80
                        ),
                        max(
                            30,
                            ball["y"] - 20
                        )
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

            # ---------------------------------------------
            # Status text
            # ---------------------------------------------

            if detected_ball:

                cv2.putText(
                    display,
                    "TARGET LOCK",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

            else:

                cv2.putText(
                    display,
                    "SEARCHING...",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )

            # ---------------------------------------------
            # Head angle
            # ---------------------------------------------

            cv2.putText(
                display,
                f"Pan: {self.current_pan}°",
                (10, display.shape[0] - 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            # ---------------------------------------------
            # Convert BGR -> RGB
            # ---------------------------------------------

            rgb = cv2.cvtColor(
                display,
                cv2.COLOR_BGR2RGB
            )

            img = Image.fromarray(
                rgb
            )

            imgtk = ImageTk.PhotoImage(
                image=img
            )

            self.video_label.imgtk = imgtk

            self.video_label.configure(
                image=imgtk
            )

        # =================================================
        # RUN AGAIN
        # =================================================

        if not self.stop_event.is_set():

            self.root.after(
                15,
                self.update_ui
            )

    # =====================================================
    # SHUTDOWN
    # =====================================================

    def on_close(self):

        print()
        print(
            "Shutting down Jeb Mission Control..."
        )

        # -------------------------------------------------
        # Stop vision thread
        # -------------------------------------------------

        self.stop_event.set()

        # -------------------------------------------------
        # Close Pico
        # -------------------------------------------------

        if self.pico is not None:

            try:
                self.pico.close()

            except Exception:
                pass

        # -------------------------------------------------
        # Destroy UI
        # -------------------------------------------------

        self.root.destroy()


# =========================================================
# PROGRAM ENTRY POINT
# =========================================================

def main():

    root = tk.Tk()

    app = RoverUI(root)

    root.mainloop()


if __name__ == "__main__":

    main()
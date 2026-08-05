# import cv2
# import time
# import serial
# from hsv_ball import detect_tennis_ball_via_colour
# from yolo_ball import TennisBallDetector
# from fusion import fuse_detections
# from network_camera import NetworkCamera

# # -------------------------------
# # INITIALIZE DETECTORS
# # -------------------------------
# tennis_detector = TennisBallDetector()
# frame_count = 0
# YOLO_INTERVAL = 5  # run YOLO every 5 frames
# last_yolo_ball = None

# try:
#     pico = serial.Serial("COM7", 115200, timeout=1)
#     print("✅ Pico Connected")
# except Exception as e:
#     pico = None
#     print(f"⚠️ Pico disconnected ({e}). Running vision loop in simulation mode.")
# # -------------------------------
# # CONNECT TO NETWORK CAMERA
# # -------------------------------
# net_cam = NetworkCamera(pi_ip="192.168.1.154", port=6000)

# last_time = time.time()
# fps = 0

# # -------------------------------
# # MAIN LOOP
# # -------------------------------
# while True:
#     try:
#         frame, distance = net_cam.read()
#         if frame is None:
#             continue
#     except (ConnectionError, TimeoutError) as e:
#         print(f"[NetworkCamera] Connection lost: {e}. Reconnecting...")
#         try:
#             net_cam.connect()
#         except Exception as conn_err:
#             print(f"[NetworkCamera] Reconnect failed: {conn_err}. Retrying in 2s...")
#             time.sleep(2)
#         continue

#     # 1. Run HSV tracking on full frame
#     hsv_ball = detect_tennis_ball_via_colour(frame)

#     # 2. Periodically run YOLO tracking on resized frame
#     frame_count += 1
#     if frame_count % YOLO_INTERVAL == 0:
#         small = cv2.resize(frame, (320, 240))
#         yolo_res = tennis_detector.detect(small)
        
#         if yolo_res:
#             # Scale coordinates up to match the full frame sizes
#             scale_x = frame.shape[1] / 320
#             scale_y = frame.shape[0] / 240
#             last_yolo_ball = {
#                 "x": int(yolo_res["x"] * scale_x),
#                 "y": int(yolo_res["y"] * scale_y),
#                 "size": int(yolo_res["size"] * (scale_x + scale_y) / 2),
#                 "confidence": yolo_res["confidence"],
#             }
#         else:
#             last_yolo_ball = None

#     # 3. Fuse the results (now both are in the same coordinate space)
#     ball = fuse_detections(hsv_ball, last_yolo_ball)

#     # 4. Rendering Annotations
#     if ball:
#         cv2.circle(frame, (ball["x"], ball["y"]), int(ball["size"]), (0, 255, 0), 2)
#         cv2.putText(frame, f"Tennis Ball {ball['confidence']:.2f} | Dist: {distance:.2f} cm",
#                     (ball["x"] - 50, ball["y"] - 20),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
#     else:
#         cv2.putText(frame, f"Distance: {distance:.2f} cm", (10, 30),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

#     # FPS Calculation
#     now = time.time()
#     fps = 0.9 * fps + 0.1 * (1 / (now - last_time))
#     last_time = now
#     cv2.putText(frame, f"FPS: {fps:.1f}", (10, frame.shape[0]-10),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#     cv2.imshow("Fusion Vision", frame)
#     if cv2.waitKey(1) & 0xFF in (ord('q'), ord('d')):
#         break

# cv2.destroyAllWindows()

import cv2
import time

from JebsEyes.hsv_ball import detect_tennis_ball_via_colour
from JebsEyes.yolo_ball import TennisBallDetector
from JebsEyes.fusion import fuse_detections
from JebsEyes.network_camera import NetworkCamera


# =========================================================
# CONFIGURATION
# =========================================================

PI_IP = "192.168.0.142"
PI_PORT = 6000

YOLO_INTERVAL = 5

DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480


# =========================================================
# INITIALIZE YOLO
# =========================================================

print("================================")
print("       JEB VISION SYSTEM")
print("================================")

print("Loading YOLO detector...")

tennis_detector = TennisBallDetector()

print("✅ YOLO detector ready")


# =========================================================
# CONNECT TO NETWORK CAMERA
# =========================================================

print()
print("Connecting to Jeb's camera...")

net_cam = NetworkCamera(
    stream_url="http://192.168.0.142:5000/video"
)

print("✅ Network camera connected")


# =========================================================
# VARIABLES
# =========================================================

frame_count = 0

last_yolo_ball = None

last_time = time.time()

fps = 0.0


# =========================================================
# MAIN VISION LOOP
# =========================================================

print()
print("================================")
print("       VISION LOOP STARTED")
print("================================")
print()
print("Press Q to quit")
print()


while True:

    # -----------------------------------------------------
    # GET FRAME FROM JEB
    # -----------------------------------------------------

    try:

        frame, distance = net_cam.read()

        if frame is None:
            continue

    except (ConnectionError, TimeoutError) as e:

        print(
            f"[NetworkCamera] Connection lost: {e}"
        )

        print("Attempting reconnect...")

        try:

            net_cam.connect()

            print("✅ Reconnected")

        except Exception as conn_err:

            print(
                f"[NetworkCamera] Reconnect failed: "
                f"{conn_err}"
            )

            time.sleep(2)

        continue


    # -----------------------------------------------------
    # FLIP CAMERA
    # -----------------------------------------------------
    #
    # Camera is physically upside down on Jeb.
    #
    # flipCode = -1 means:
    #   flip horizontally AND vertically
    #
    # -----------------------------------------------------

    # frame = cv2.flip(frame, -1) # Hey Michael, I commented this out because the camera is now mounted correctly on Jeb. -Jordan


    # -----------------------------------------------------
    # HSV DETECTION
    # -----------------------------------------------------

    hsv_ball = detect_tennis_ball_via_colour(frame)


    # -----------------------------------------------------
    # YOLO DETECTION
    # -----------------------------------------------------

    frame_count += 1

    if frame_count % YOLO_INTERVAL == 0:

        small = cv2.resize(
            frame,
            (320, 240)
        )

        yolo_res = tennis_detector.detect(
            small
        )


        if yolo_res:

            scale_x = (
                frame.shape[1] / 320
            )

            scale_y = (
                frame.shape[0] / 240
            )

            last_yolo_ball = {

                "x": int(
                    yolo_res["x"] * scale_x
                ),

                "y": int(
                    yolo_res["y"] * scale_y
                ),

                "size": int(
                    yolo_res["size"]
                    * (scale_x + scale_y)
                    / 2
                ),

                "confidence":
                    yolo_res["confidence"],
            }

        else:

            last_yolo_ball = None


    # -----------------------------------------------------
    # FUSE HSV + YOLO
    # -----------------------------------------------------

    ball = fuse_detections(
        hsv_ball,
        last_yolo_ball
    )


    # -----------------------------------------------------
    # DRAW DETECTION
    # -----------------------------------------------------

    if ball:

        x = ball["x"]
        y = ball["y"]
        size = int(ball["size"])

        confidence = ball["confidence"]


        # Detection circle

        cv2.circle(
            frame,
            (x, y),
            size,
            (0, 255, 0),
            2
        )


        # Detection centre

        cv2.circle(
            frame,
            (x, y),
            4,
            (0, 0, 255),
            -1
        )


        # Detection information

        if distance is not None:

            text = (
                f"Tennis Ball "
                f"{confidence:.2f} | "
                f"Dist: {distance:.1f} cm"
            )

        else:

            text = (
                f"Tennis Ball "
                f"{confidence:.2f}"
            )


        cv2.putText(
            frame,
            text,
            (max(10, x - 100), max(25, y - 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )


    # -----------------------------------------------------
    # DISTANCE DISPLAY
    # -----------------------------------------------------

    if distance is not None:

        cv2.putText(
            frame,
            f"Distance: {distance:.1f} cm",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )


    # -----------------------------------------------------
    # FPS
    # -----------------------------------------------------

    now = time.time()

    dt = now - last_time

    if dt > 0:

        current_fps = 1 / dt

        fps = (
            0.9 * fps
            + 0.1 * current_fps
        )

    last_time = now


    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (10, frame.shape[0] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        2
    )


    # -----------------------------------------------------
    # SHOW VIDEO
    # -----------------------------------------------------

    cv2.imshow(
        "Jeb Vision",
        frame
    )


    # -----------------------------------------------------
    # EXIT
    # -----------------------------------------------------

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):

        break


# =========================================================
# CLEANUP
# =========================================================

cv2.destroyAllWindows()

print()
print("Jeb Vision System stopped.")
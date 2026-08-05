import cv2
import time
import numpy as np
from JebsEyes.fusion import fuse_detections
from JebsEyes.hsv_ball import detect_tennis_ball_via_colour
from JebsEyes.yolo_ball import TennisBallDetector

def open_camera():
    for index in [1, 0, 2, 3]:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✅ Camera found on index {index}")
                return cap, index
            cap.release()
    return None, None

def vision_loop(state, stop_event):
    WIDTH = 640
    HEIGHT = 480

    cap, CAMERA_INDEX = open_camera()

    if cap is None:
        print("⚠️ No camera found. Using simulation mode.")
        use_camera = False
    else:
        print("✅ Real camera successfully locked.")
        use_camera = True
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    tennis_detector = TennisBallDetector()
    frame_count = 0
    YOLO_INTERVAL = 5
    last_yolo_ball = None

    print("✅ Vision thread started")

    while not stop_event.is_set():
        if use_camera:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("⚠️ Failed to read frame")
                time.sleep(0.01)
                continue
            
            # Target Detection Mechanics
            hsv_ball = detect_tennis_ball_via_colour(frame)
            
            frame_count += 1
            if frame_count % YOLO_INTERVAL == 0:
                small = cv2.resize(frame, (320, 240))
                yolo_ball = tennis_detector.detect(small)

                if yolo_ball:
                    scale_x = frame.shape[1] / 320
                    scale_y = frame.shape[0] / 240
                    last_yolo_ball = {
                        "x": int(yolo_ball["x"] * scale_x),
                        "y": int(yolo_ball["y"] * scale_y),
                        "size": int(yolo_ball["size"] * (scale_x + scale_y) / 2),
                        "confidence": yolo_ball["confidence"],
                    }
                else:
                    last_yolo_ball = None

            ball = fuse_detections(hsv_ball, last_yolo_ball)

        else:
            # Simulation Mode
            frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            cv2.putText(frame, "SIMULATION MODE", (100, 220),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            ball = None

        # --- WRITE INTO SHARED STATE Safely ---
        with state.lock:
            state.frame = frame.copy() if frame is not None else None
            if ball:
                state.ball_detected = True
                state.ball_x = ball["x"]
                state.ball_y = ball["y"]
                state.ball_confidence = ball["confidence"]
            else:
                state.ball_detected = False

        time.sleep(0.01)

    if cap is not None:
        cap.release()
    print("🛑 Vision thread stopped")
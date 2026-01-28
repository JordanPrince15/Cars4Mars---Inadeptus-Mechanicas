# # import cv2
# # import time
# # from fusion import fuse_detections
# # from hsv_ball import detect_tennis_ball_via_colour
# # from yolo_ball import TennisBallDetector

# # # Try 0 first (built-in webcam). If black screen, try 1 or 2.
# # CAMERA_INDEX = 0
# # WIDTH = 640
# # HEIGHT = 480

# # tennis_detector = TennisBallDetector()
# # frame_count = 0
# # YOLO_INTERVAL = 5  # run YOLO every 5 frames
# # last_yolo_ball = None

# # cap = cv2.VideoCapture(CAMERA_INDEX)

# # last_time = time.time()
# # fps = 0.0

# # if not cap.isOpened():
# #     raise RuntimeError("❌ Could not open webcam")

# # cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
# # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

# # print("✅ Webcam opened successfully")
# # print("Press 'q' to quit")

# # while True:
# #     ret, frame = cap.read()
# #     if not ret or frame is None:
# #         continue

# #     yolo_ball = None  # ✅ ALWAYS defined

# #     hsv_ball = detect_tennis_ball_via_colour(frame)

# #     ball = fuse_detections(hsv_ball, last_yolo_ball)

# #     if ball:
# #         cv2.putText(frame, f"Tennis Ball {ball['confidence']:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
# #     frame_count += 1
# #     if frame_count % YOLO_INTERVAL == 0:
# #         small = cv2.resize(frame, (320, 240))
# #         yolo_ball = tennis_detector.detect(small)

# #         if yolo_ball:
# #             scale_x = frame.shape[1] / 320
# #             scale_y = frame.shape[0] / 240

# #             last_yolo_ball = {
# #                 "x": int(yolo_ball["x"] * scale_x),
# #                 "y": int(yolo_ball["y"] * scale_y),
# #                 "size": int(yolo_ball["size"] * (scale_x + scale_y) / 2),
# #                 "confidence": yolo_ball["confidence"],
# #             }

# #     # --- Drawing ---
# #     if last_yolo_ball:
# #         cv2.circle(
# #             frame,
# #             (last_yolo_ball["x"], last_yolo_ball["y"]),
# #             last_yolo_ball["size"],
# #             (0, 255, 0),
# #             2
# #         )


# #     now = time.time()
# #     fps = 0.9 * fps + 0.1 * (1 / (now - last_time))
# #     last_time = now

# #     cv2.imshow("Laptop Webcam Test", frame)

# #     if cv2.waitKey(1) & 0xFF == ord('q'):
# #         break

# # cap.release()
# # cv2.destroyAllWindows()
# # print("🛑 Webcam closed")


# import cv2
# import time

# from JebsEyes.robot_state import RobotState
# from JebsEyes.fusion import fuse_detections
# from JebsEyes.hsv_ball import detect_tennis_ball_via_colour
# from JebsEyes.yolo_ball import TennisBallDetector
# # from robot_state import RobotState
# import threading




# def vision_loop(state: RobotState, stop_event: threading.Event):

#     CAMERA_INDEX = 0
#     WIDTH = 640
#     HEIGHT = 480
#     YOLO_INTERVAL = 5

#     tennis_detector = TennisBallDetector()
#     frame_count = 0
#     last_yolo_ball = None


#     cap = cv2.VideoCapture(CAMERA_INDEX)
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    
#     cap = cv2.VideoCapture(CAMERA_INDEX)
#     if not cap.isOpened():
#         raise RuntimeError("❌ Could not open webcam")

#     print("✅ Vision loop started")

#     while not stop_event.is_set():
#         ret, frame = cap.read()
#         if not ret or frame is None:
#             continue

#         hsv_ball = detect_tennis_ball_via_colour(frame)

#         ball = fuse_detections(hsv_ball, last_yolo_ball)

#         frame_count += 1
#         if frame_count % YOLO_INTERVAL == 0:
#             small = cv2.resize(frame, (320, 240))
#             yolo_ball = tennis_detector.detect(small)

#             if yolo_ball:
#                 scale_x = frame.shape[1] / 320
#                 scale_y = frame.shape[0] / 240

#                 last_yolo_ball = {
#                     "x": int(yolo_ball["x"] * scale_x),
#                     "y": int(yolo_ball["y"] * scale_y),
#                     "size": int(yolo_ball["size"] * (scale_x + scale_y) / 2),
#                     "confidence": yolo_ball["confidence"],
#                 }
#             else:
#                 last_yolo_ball = None

#         # --- Update shared state ---
#         with state.lock:
#             state.frame = frame.copy()
#             state.ball = ball

#             # Map x-position → yaw (simple, tweak later)
#             if ball:
#                 center_x = frame.shape[1] / 2
#                 error = ball["x"] - center_x
#                 state.camera_yaw = error * 0.05  # gain

#     cap.release()
#     print("🛑 Vision loop stopped")


# # Standalone test runner
# if __name__ == "__main__":
#     state = RobotState()
#     stop_event = threading.Event()

#     t = threading.Thread(target=vision_loop, args=(state, stop_event), daemon=True)
#     t.start()

#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         stop_event.set()
#         t.join()


import cv2
import time

from JebsEyes.fusion import fuse_detections
from JebsEyes.hsv_ball import detect_tennis_ball_via_colour
from JebsEyes.yolo_ball import TennisBallDetector


def vision_loop(state, stop_event):
    CAMERA_INDEX = 0
    # WIDTH = 640
    # HEIGHT = 480
    WIDTH = 320/2
    HEIGHT = 240/2

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    if not cap.isOpened():
        print("❌ Could not open webcam")
        return

    tennis_detector = TennisBallDetector()
    frame_count = 0
    YOLO_INTERVAL = 5
    last_yolo_ball = None

    print("✅ Vision thread started")

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        hsv_ball = detect_tennis_ball_via_colour(frame)
        ball = fuse_detections(hsv_ball, last_yolo_ball)

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

        # --- WRITE INTO SHARED STATE ---
        with state.lock:
            state.frame = frame.copy()

            if ball:
                state.ball_detected = True
                state.ball_x = ball["x"]
                state.ball_y = ball["y"]
                state.ball_confidence = ball["confidence"]
            else:
                state.ball_detected = False

        time.sleep(0.01)

    cap.release()
    print("🛑 Vision thread stopped")

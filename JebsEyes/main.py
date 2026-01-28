# import cv2
# import time
# from hsv_ball import detect_tennis_ball_via_colour
# from yolo_ball import TennisBallDetector
# from hammer_yolo import HammerDetector
# from fusion import fuse_detections

# from network_camera import NetworkCamera  # network camera helper

# # -------------------------------
# # TIME OPTIMALIZATION
# # -------------------------------

# # -------------------------------
# # INITIALIZE DETECTORS
# # -------------------------------
# tennis_detector = TennisBallDetector()
# hammer_detector = HammerDetector()
# frame_count = 0
# YOLO_INTERVAL = 5  # run YOLO every 5 frames
# last_yolo_ball = None
# last_hammer = None


# # -------------------------------
# # CONNECT TO NETWORK CAMERA
# # -------------------------------

# last_time = time.time()
# fps = 0

# net_cam = NetworkCamera(pi_ip="192.168.1.154", port=6000)
# net_cam.sock.setblocking(False)


# # -------------------------------
# # MAIN LOOP
# # -------------------------------
    

# while True:
#     try:
#         frame, distance = net_cam.read()
#         if frame is None:
#             continue  # wait for full packet
#     except ConnectionError:
#         print("Lost connection, reconnecting...")
#         net_cam.connect()
#         continue

#     hsv_ball = detect_tennis_ball_via_colour(frame)

#     frame_count += 1
#     if frame_count % YOLO_INTERVAL == 0:
#         small = cv2.resize(frame, (320, 240))
#         last_yolo_ball = tennis_detector.detect(small)
#         last_hammer = hammer_detector.detect(small)

#     ball = fuse_detections(hsv_ball, last_yolo_ball)

#     if last_hammer:
#         cv2.circle(frame, (...))

#     if ball:
#         cv2.putText(frame, ...)

#     # FPS calc + display
#     now = time.time()
#     fps = 0.9 * fps + 0.1 * (1 / (now - last_time))
#     last_time = now

#     cv2.imshow("Fusion Vision", frame)

#     if cv2.waitKey(1) & 0xFF in (ord('q'), ord('d')):
#         break

# # while True:
# #     # try:
# #     #     frame, distance = net_cam.read()  # Get frame + distance
# #     # except ConnectionError:
# #     #     print("Lost connection, reconnecting...")
# #     #     net_cam.connect()
# #     #     continue
# #     try:
# #         frame, distance = net_cam.read()
# #     except (BlockingIOError, ConnectionError):
# #         continue


# #     # -------------------------------
# #     # HSV BALL DETECTION
# #     # -------------------------------
# #     hsv_ball = detect_tennis_ball_via_colour(frame)

# #     # -------------------------------
# #     # YOLO TENNIS BALL DETECTION
# #     # -------------------------------
# #     frame_count += 1

# #     if frame_count % YOLO_INTERVAL == 0:
# #         last_yolo_ball = tennis_detector.detect(frame)
# #         last_hammer = hammer_detector.detect(frame)

# #     yolo_ball = last_yolo_ball
# #     hammer = last_hammer

# #     if hammer:
# #         cv2.circle(frame, (hammer["x"], hammer["y"]), int(hammer["size"]), (0, 0, 255), 2)
# #         cv2.putText(
# #             frame,
# #             f"Hammer {hammer['confidence']:.2f}",
# #             (hammer["x"] - 50, hammer["y"] - 20),
# #             cv2.FONT_HERSHEY_SIMPLEX,
# #             0.6,
# #             (255, 255, 255),
# #             2
# #         )

# #     # -------------------------------
# #     # FUSE BALL DETECTIONS
# #     # -------------------------------
# #     ball = fuse_detections(hsv_ball, yolo_ball)
# #     if ball:
# #         cv2.circle(frame, (ball["x"], ball["y"]), int(ball["size"]), (0, 255, 0), 2)
# #         cv2.putText(
# #             frame,
# #             f"Tennis Ball {ball['confidence']:.2f} | Dist: {distance:.2f} cm",
# #             (ball["x"] - 50, ball["y"] - 20),
# #             cv2.FONT_HERSHEY_SIMPLEX,
# #             0.6,
# #             (255, 255, 255),
# #             2
# #         )
# #     else:
# #         # Still show distance even if no ball detected
# #         cv2.putText(
# #             frame,
# #             f"Distance: {distance:.2f} cm",
# #             (10, 30),
# #             cv2.FONT_HERSHEY_SIMPLEX,
# #             0.7,
# #             (255, 255, 255),
# #             2
# #         )

# #     now = time.time()
# #     fps = 0.9 * fps + 0.1 * (1 / (now - last_time))
# #     last_time = now

# #     cv2.putText(
# #         frame,
# #         f"FPS: {fps:.1f}",
# #         (10, frame.shape[0] - 10),
# #         cv2.FONT_HERSHEY_SIMPLEX,
# #         0.5,
# #         (0, 255, 0),
# #         2
# #     )


# #     # -------------------------------
# #     # DISPLAY
# #     # -------------------------------
# #     cv2.imshow("Fusion Vision", frame)

# #     # Quit on 'q' or 'd'
# #     if cv2.waitKey(1) & 0xFF in (ord('q'), ord('d')):
# #         break

# # # -------------------------------
# # # CLEANUP
# # # -------------------------------
# cv2.destroyAllWindows()


import cv2
import time
from hsv_ball import detect_tennis_ball_via_colour
from yolo_ball import TennisBallDetector
# from hammer_yolo import HammerDetector
from fusion import fuse_detections
from network_camera import NetworkCamera

# -------------------------------
# INITIALIZE DETECTORS
# -------------------------------
tennis_detector = TennisBallDetector()
# hammer_detector = HammerDetector()
frame_count = 0
YOLO_INTERVAL = 5  # run YOLO every 5 frames
last_yolo_ball = None
last_hammer = None

# -------------------------------
# CONNECT TO NETWORK CAMERA
# -------------------------------
net_cam = NetworkCamera(pi_ip="192.168.1.154", port=6000)

last_time = time.time()
fps = 0

# -------------------------------
# MAIN LOOP
# -------------------------------


while True:
    try:
        frame, distance = net_cam.read()

        if frame is None:
            # partial/invalid data, skip and try next
            continue

    except (ConnectionError, TimeoutError) as e:
        print(f"[NetworkCamera] Connection lost: {e}. Reconnecting...")
        try:
            net_cam.connect()
        except Exception as conn_err:
            print(f"[NetworkCamera] Reconnect failed: {conn_err}. Retrying in 2s...")
            import time; time.sleep(2)
        continue

    # At this point, frame is valid
    # Your existing processing:
    hsv_ball = detect_tennis_ball_via_colour(frame)

    frame_count += 1
    if frame_count % YOLO_INTERVAL == 0:
        small = cv2.resize(frame, (320, 240))
        last_yolo_ball = tennis_detector.detect(small)
       # last_hammer = hammer_detector.detect(small)

    ball = fuse_detections(hsv_ball, last_yolo_ball)

    # Drawing code here ...
    # if last_hammer:
    #     cv2.circle(frame, (last_hammer["x"], last_hammer["y"]), int(last_hammer["size"]), (0, 0, 255), 2)
    #     cv2.putText(frame, f"Hammer {last_hammer['confidence']:.2f}",
    #                 (last_hammer["x"] - 50, last_hammer["y"] - 20),
    #                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    if ball:
        cv2.circle(frame, (ball["x"], ball["y"]), int(ball["size"]), (0, 255, 0), 2)
        cv2.putText(frame, f"Tennis Ball {ball['confidence']:.2f} | Dist: {distance:.2f} cm",
                    (ball["x"] - 50, ball["y"] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    else:
        cv2.putText(frame, f"Distance: {distance:.2f} cm", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # FPS calculation
    now = time.time()
    fps = 0.9 * fps + 0.1 * (1 / (now - last_time))
    last_time = now
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, frame.shape[0]-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display
    cv2.imshow("Fusion Vision", frame)
    if cv2.waitKey(1) & 0xFF in (ord('q'), ord('d')):
        break


cv2.destroyAllWindows()

 
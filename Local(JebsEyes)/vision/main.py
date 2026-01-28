import cv2
from hsv_ball import detect_tennis_ball_via_colour
from yolo_ball import TennisBallDetector
from hammer_yolo import HammerDetector
from fusion import fuse_detections

from network_camera import NetworkCamera  # network camera helper

# -------------------------------
# INITIALIZE DETECTORS
# -------------------------------
tennis_detector = TennisBallDetector()
hammer_detector = HammerDetector()

# -------------------------------
# CONNECT TO NETWORK CAMERA
# -------------------------------
net_cam = NetworkCamera(pi_ip="192.168.1.154", port=6000)

# -------------------------------
# MAIN LOOP
# -------------------------------
while True:
    try:
        frame, distance = net_cam.read()  # Get frame + distance
    except ConnectionError:
        print("Lost connection, reconnecting...")
        net_cam.connect()
        continue

    # -------------------------------
    # HSV BALL DETECTION
    # -------------------------------
    hsv_ball = detect_tennis_ball_via_colour(frame)

    # -------------------------------
    # YOLO TENNIS BALL DETECTION
    # -------------------------------
    yolo_ball = tennis_detector.detect(frame)

    # -------------------------------
    # HAMMER DETECTION
    # -------------------------------
    hammer = hammer_detector.detect(frame)
    if hammer:
        cv2.circle(frame, (hammer["x"], hammer["y"]), int(hammer["size"]), (0, 0, 255), 2)
        cv2.putText(
            frame,
            f"Hammer {hammer['confidence']:.2f}",
            (hammer["x"] - 50, hammer["y"] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

    # -------------------------------
    # FUSE BALL DETECTIONS
    # -------------------------------
    ball = fuse_detections(hsv_ball, yolo_ball)
    if ball:
        cv2.circle(frame, (ball["x"], ball["y"]), int(ball["size"]), (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"Tennis Ball {ball['confidence']:.2f} | Dist: {distance:.2f} cm",
            (ball["x"] - 50, ball["y"] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )
    else:
        # Still show distance even if no ball detected
        cv2.putText(
            frame,
            f"Distance: {distance:.2f} cm",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    # -------------------------------
    # DISPLAY
    # -------------------------------
    cv2.imshow("Fusion Vision", frame)

    # Quit on 'q' or 'd'
    if cv2.waitKey(1) & 0xFF in (ord('q'), ord('d')):
        break

# -------------------------------
# CLEANUP
# -------------------------------
cv2.destroyAllWindows()

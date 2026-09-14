import cv2

from JebsEyes.hsv_ball import detect_tennis_ball_via_colour
from JebsEyes.yolo_ball import TennisBallDetector
from JebsEyes.hammer_yolo import HammerDetector 
from JebsEyes.fusion import fuse_detections


class ObjectMission:
    """
    Handles the autonomous object-detection mission.

    Currently:
        - Tennis ball detection
        - Tennis ball LEFT / CENTRE / RIGHT positioning

    Later:
        - Traffic cone detection
        - Hammer detection
    """

    def __init__(self):
        # =================================================
        # TENNIS BALL DETECTOR
        # =================================================
        self.hammer_detector = HammerDetector()
        self.tennis_detector = TennisBallDetector()

        # Last successful YOLO detection.
        # We keep this between frames because YOLO does not
        # necessarily run on every camera frame.
        self.last_yolo = None

        self.frame_counter = 0

        # =================================================
        # STEERING
        # =================================================

        self.deadzone = 40

        # Current simulated/commanded camera pan position.
        self.current_pan = 0

        print("Object mission initialized.")

    # =====================================================
    # DETECTION
    # =====================================================

    def detect(self, frame):
        """
        Detect a tennis ball in the supplied frame.

        Returns:
            Ball detection dictionary, or None.
        """

        # -------------------------------------------------
        # HSV detection
        # -------------------------------------------------

        hsv_ball = detect_tennis_ball_via_colour(frame)

        # -------------------------------------------------
        # YOLO detection
        #
        # Run periodically to reduce CPU usage.
        # -------------------------------------------------

        self.frame_counter += 1

        if self.frame_counter % 5 == 0: #change back to 30 later 

            # Resize before YOLO inference to reduce CPU load.
            small = cv2.resize(
                frame,
                (320, 240)
            )

            yolo = self.tennis_detector.detect(small)

            if yolo:
                scale_x = frame.shape[1] / 320
                scale_y = frame.shape[0] / 240

                self.last_yolo = {
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
                self.last_yolo = None

        # -------------------------------------------------
        # Fuse HSV + YOLO
        # -------------------------------------------------

        ball = fuse_detections(
            hsv_ball,
            self.last_yolo
        )

        return ball

    # =====================================================
    # POSITION
    # =====================================================

    def get_direction(self, x, frame_width):
        """
        Determine whether the tennis ball is LEFT,
        CENTRE or RIGHT of the camera.

        Uses the actual frame width rather than assuming
        the camera is always 640 pixels wide.
        """

        frame_center = frame_width / 2

        error = x - frame_center

        if error < -self.deadzone:
            return "LEFT"

        elif error > self.deadzone:
            return "RIGHT"

        else:
            return "CENTRE"

    # =====================================================
    # STEERING DECISION
    # =====================================================

    def get_action(self, ball, frame_width):
        """
        Decide what the rover/head should do based on
        tennis-ball position.

        Returns:
            "LEFT"
            "RIGHT"
            "CENTRE"
            None
        """

        if ball is None:
            return None

        direction = self.get_direction(
            ball["x"],
            frame_width
        )

        # -------------------------------------------------
        # LEFT
        # -------------------------------------------------

        if direction == "LEFT":
            self.current_pan -= 2
            return "LEFT"

        # -------------------------------------------------
        # RIGHT
        # -------------------------------------------------

        elif direction == "RIGHT":
            self.current_pan += 2
            return "RIGHT"

        # -------------------------------------------------
        # CENTRE
        # -------------------------------------------------

        return "CENTRE"

    # =====================================================
    # PROCESS FRAME
    # =====================================================

    def process_frame(self, frame):
        """
        Complete object-mission processing for one frame.

        Returns:
            {
                "ball": detection or None,
                "direction": "LEFT"/"CENTRE"/"RIGHT"/None,
                "action": "LEFT"/"RIGHT"/"CENTRE"/None
            }
        """

        ball = self.detect(frame)

        if ball is not None:
            direction = self.get_direction(
                ball["x"],
                frame.shape[1]
            )

            action = self.get_action(
                ball,
                frame.shape[1]
            )

        else:
            direction = None
            action = None

        return {
            "ball": ball,
            "direction": direction,
            "action": action
        }
import cv2

from JebsEyes.hsv_ball import detect_tennis_ball_via_colour
from JebsEyes.yolo_ball import TennisBallDetector
from JebsEyes.hammer_yolo import HammerDetector 
from JebsEyes.cone_yolo import ConeDetector
from JebsEyes.fusion import fuse_detections


class ObjectMission:
    TEST_HAMMER = True
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
        self.cone_detector = ConeDetector()

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
        Runs the tennis-ball, hammer, and traffic-cone detectors.

        Each detected object is drawn on the frame and classified
        as LEFT, CENTER, or RIGHT based on its horizontal position.
        """

        # ==================================================
        # TENNIS BALL
        # ==================================================

        ball = self.detect(frame)

        # ==================================================
        # HAMMER + CONE
        # ==================================================

        hammers = self.hammer_detector.detect(frame)
        cones = self.cone_detector.detect(frame)

        # ==================================================
        # HELPER: DETERMINE LEFT / CENTER / RIGHT
        # ==================================================

        screen_width = frame.shape[1]

        def get_position(x):
            if x < screen_width / 3:
                return "LEFT"
            elif x < 2 * screen_width / 3:
                return "CENTER"
            else:
                return "RIGHT"

        # ==================================================
        # DRAW TENNIS BALL
        # ==================================================

        if ball:

            x = ball["x"]
            y = ball["y"]
            size = ball["size"]
            confidence = ball["confidence"]

            position = get_position(x)

            radius = max(5, int(size / 2))

            cv2.circle(
                frame,
                (x, y),
                radius,
                (0, 255, 0),
                3
            )

            label = f"TENNIS BALL {confidence:.0%} - {position}"

            cv2.putText(
                frame,
                label,
                (max(5, x - radius), max(30, y - radius - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

        # ==================================================
        # DRAW HAMMERS
        # ==================================================

        for detection in hammers:

            x = detection["x"]
            y = detection["y"]
            width = detection["width"]
            height = detection["height"]
            confidence = detection["confidence"]

            position = get_position(x)

            x1 = int(x - width / 2)
            y1 = int(y - height / 2)
            x2 = int(x + width / 2)
            y2 = int(y + height / 2)

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame.shape[1] - 1, x2)
            y2 = min(frame.shape[0] - 1, y2)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 0, 255),
                3
            )

            label = f"HAMMER {confidence:.0%} - {position}"

            cv2.putText(
                frame,
                label,
                (x1, max(30, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 0, 255),
                2
            )

        # ==================================================
        # DRAW TRAFFIC CONES
        # ==================================================

        for detection in cones:

            x = detection["x"]
            y = detection["y"]
            width = detection["width"]
            height = detection["height"]
            confidence = detection["confidence"]

            position = get_position(x)

            x1 = int(x - width / 2)
            y1 = int(y - height / 2)
            x2 = int(x + width / 2)
            y2 = int(y + height / 2)

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame.shape[1] - 1, x2)
            y2 = min(frame.shape[0] - 1, y2)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 165, 255),
                3
            )

            label = f"TRAFFIC CONE {confidence:.0%} - {position}"

            cv2.putText(
                frame,
                label,
                (x1, max(30, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 165, 255),
                2
            )

        # ==================================================
        # RETURN EVERYTHING
        # ==================================================

        return {
            "ball": ball,
            "direction": get_position(ball["x"]) if ball else None,
            "action": None,
            "hammers": hammers,
            "cones": cones
        }



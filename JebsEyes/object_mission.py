
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
        - Hammer detection
        - Traffic cone detection
        - LEFT / CENTRE / RIGHT positioning
        - Temporal detection stabilisation
    """

    def __init__(self):

        # =================================================
        # OBJECT DETECTORS
        # =================================================

        self.hammer_detector = HammerDetector()
        self.tennis_detector = TennisBallDetector()
        self.cone_detector = ConeDetector()

        # =================================================
        # TENNIS BALL YOLO MEMORY
        # =================================================

        # Last successful YOLO detection.
        # We keep this between frames because YOLO does not
        # necessarily run on every camera frame.
        self.last_yolo = None

        self.frame_counter = 0

        # =================================================
        # TEMPORAL DETECTION STABILITY
        # =================================================

        # Last stable detection for each object.
        self.stable_detections = {
            "tennis_ball": None,
            "hammer": None,
            "traffic_cone": None
        }

        # Number of consecutive frames where an object
        # has been detected.
        self.detection_counts = {
            "tennis_ball": 0,
            "hammer": 0,
            "traffic_cone": 0
        }

        # Number of consecutive frames where an object
        # has NOT been detected.
        self.missed_counts = {
            "tennis_ball": 0,
            "hammer": 0,
            "traffic_cone": 0
        }

        # Number of consecutive detections required
        # before a new object is considered confirmed.
        self.confirm_frames = 2

        # Number of missed frames tolerated before
        # removing an existing detection.
        self.max_missed_frames = 3

        # Position smoothing.
        #
        # 0.35 means:
        #     35% new position
        #     65% previous position
        #
        # Smaller = smoother
        # Larger = more responsive
        self.position_smoothing = 0.35

        # =================================================
        # STEERING
        # =================================================

        self.deadzone = 40

        # Current simulated/commanded camera pan position.
        self.current_pan = 0

        print("Object mission initialized.")

    def load_venue_weights(self, class_name, weights_path):
        """
        Reload a detector with weights fine-tuned on venue photos.
        """

        name = class_name.strip().lower().replace(" ", "_")

        if name == "hammer":
            self.hammer_detector = HammerDetector(
                model_path=weights_path
            )
            return "Hammer detector now uses the venue-trained weights."

        if name in ("cone", "traffic_cone"):
            self.cone_detector = ConeDetector(
                model_path=weights_path
            )
            return "Cone detector now uses the venue-trained weights."

        return (
            f"Weights saved for '{class_name}'. "
            "Live Detect still uses the existing detectors "
            "until this class is wired in."
        )

    # =====================================================
    # TENNIS BALL DETECTION
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

        if self.frame_counter % 5 == 0:  # change back to 30 later

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
    # TEMPORAL STABILISATION
    # =====================================================

    def stabilise_detection(self, detection, object_class):
        """
        Stabilise a single object detection over time.

        A detection must appear for several consecutive
        frames before being accepted.

        Once accepted, a few missed frames are tolerated.

        The x/y position is also smoothed to reduce jitter.
        """

        # =================================================
        # OBJECT DETECTED
        # =================================================

        if detection is not None:

            # Reset missed-frame counter.
            self.missed_counts[object_class] = 0

            # Increase consecutive detection count.
            self.detection_counts[object_class] += 1

            # -------------------------------------------------
            # NO CURRENT STABLE DETECTION
            # -------------------------------------------------

            if self.stable_detections[object_class] is None:

                # Require multiple consecutive detections.
                if (
                    self.detection_counts[object_class]
                    >= self.confirm_frames
                ):

                    self.stable_detections[object_class] = (
                        detection.copy()
                    )

                else:
                    return None

            # -------------------------------------------------
            # ALREADY HAVE A STABLE DETECTION
            # -------------------------------------------------

            else:

                old = self.stable_detections[object_class]

                # -------------------------------------------------
                # SMOOTH X POSITION
                # -------------------------------------------------

                old_x = old["x"]
                new_x = detection["x"]

                smoothed_x = int(
                    old_x * (1 - self.position_smoothing)
                    + new_x * self.position_smoothing
                )

                # -------------------------------------------------
                # SMOOTH Y POSITION
                # -------------------------------------------------

                old_y = old["y"]
                new_y = detection["y"]

                smoothed_y = int(
                    old_y * (1 - self.position_smoothing)
                    + new_y * self.position_smoothing
                )

                # Update the detection.
                detection = detection.copy()

                detection["x"] = smoothed_x
                detection["y"] = smoothed_y

                self.stable_detections[object_class] = detection

            return self.stable_detections[object_class]

        # =================================================
        # OBJECT NOT DETECTED
        # =================================================

        self.detection_counts[object_class] = 0

        self.missed_counts[object_class] += 1

        # -------------------------------------------------
        # TEMPORARILY KEEP LAST DETECTION
        # -------------------------------------------------

        if (
            self.stable_detections[object_class] is not None
            and
            self.missed_counts[object_class]
            <= self.max_missed_frames
        ):

            return self.stable_detections[object_class]

        # -------------------------------------------------
        # OBJECT HAS ACTUALLY DISAPPEARED
        # -------------------------------------------------

        self.stable_detections[object_class] = None
        self.missed_counts[object_class] = 0

        return None

    # =====================================================
    # POSITION
    # =====================================================

    def get_direction(self, x, frame_width):
        """
        Determine whether an object is LEFT,
        CENTRE or RIGHT of the camera.

        Uses the actual frame width.
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
        Runs the tennis-ball, hammer, and traffic-cone
        detectors.

        Temporal filtering is applied to reduce detection
        jitter and prevent single-frame detection failures.
        """

        # =================================================
        # RAW DETECTIONS
        # =================================================

        ball_raw = self.detect(frame)

        hammers_raw = self.hammer_detector.detect(frame)

        cones_raw = self.cone_detector.detect(frame)

        # =================================================
        # SELECT BEST HAMMER
        # =================================================

        hammer_raw = None

        if hammers_raw:

            hammer_raw = max(
                hammers_raw,
                key=lambda d: d["confidence"]
            )

        # =================================================
        # SELECT BEST CONE
        # =================================================

        cone_raw = None

        if cones_raw:

            cone_raw = max(
                cones_raw,
                key=lambda d: d["confidence"]
            )

        # =================================================
        # STABILISE EACH OBJECT
        # =================================================

        ball = self.stabilise_detection(
            ball_raw,
            "tennis_ball"
        )

        hammer = self.stabilise_detection(
            hammer_raw,
            "hammer"
        )

        cone = self.stabilise_detection(
            cone_raw,
            "traffic_cone"
        )

        # =================================================
        # SCREEN POSITION
        # =================================================

        screen_width = frame.shape[1]

        def get_position(x):

            if x < screen_width / 3:
                return "LEFT"

            elif x < 2 * screen_width / 3:
                return "CENTER"

            else:
                return "RIGHT"

        # =================================================
        # DRAW TENNIS BALL
        # =================================================

        if ball:

            x = ball["x"]
            y = ball["y"]
            size = ball["size"]
            confidence = ball["confidence"]

            position = get_position(x)

            radius = max(
                5,
                int(size / 2)
            )

            cv2.circle(
                frame,
                (x, y),
                radius,
                (0, 255, 0),
                3
            )

            label = (
                f"TENNIS BALL "
                f"{confidence:.0%} - {position}"
            )

            cv2.putText(
                frame,
                label,
                (
                    max(5, x - radius),
                    max(30, y - radius - 10)
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

        # =================================================
        # DRAW HAMMER
        # =================================================

        if hammer:

            x = hammer["x"]
            y = hammer["y"]
            width = hammer["width"]
            height = hammer["height"]
            confidence = hammer["confidence"]

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

            label = (
                f"HAMMER "
                f"{confidence:.0%} - {position}"
            )

            cv2.putText(
                frame,
                label,
                (
                    x1,
                    max(30, y1 - 10)
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 0, 255),
                2
            )

        # =================================================
        # DRAW TRAFFIC CONE
        # =================================================

        if cone:

            x = cone["x"]
            y = cone["y"]
            width = cone["width"]
            height = cone["height"]
            confidence = cone["confidence"]

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

            label = (
                f"TRAFFIC CONE "
                f"{confidence:.0%} - {position}"
            )

            cv2.putText(
                frame,
                label,
                (
                    x1,
                    max(30, y1 - 10)
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 165, 255),
                2
            )

        # =================================================
        # DEBUG
        # =================================================

        print(
            f"[BALL] {'YES' if ball else 'NO'} | "
            f"[HAMMER] {'YES' if hammer else 'NO'} | "
            f"[CONE] {'YES' if cone else 'NO'}"
        )

        # =================================================
        # RETURN EVERYTHING
        # =================================================

        return {
            "ball": ball,

            "direction":
                get_position(ball["x"])
                if ball else None,

            "action": None,

            "hammers":
                [hammer]
                if hammer else [],

            "cones":
                [cone]
                if cone else []
        }


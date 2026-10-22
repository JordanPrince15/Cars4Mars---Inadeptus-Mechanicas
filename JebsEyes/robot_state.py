import threading


class RobotState:
    def __init__(self):
        self.lock = threading.Lock()

        # =================================================
        # MISSION CONTROL
        # =================================================

        # MANUAL or AUTONOMOUS
        self.control_mode = "MANUAL"

        # OBJECTS or BALLOONS
        self.mission = "OBJECTS"

        # =================================================
        # VISION
        # =================================================

        self.frame = None
        # Camera frame before detection overlays are drawn.
        self.raw_frame = None

        # live = object detection is running
        # train = Train page is open; detectors stay off
        self.ui_mode = "live"
        self.detection_enabled = True

        # Tennis ball
        self.ball_detected = False
        self.ball_x = 0
        self.ball_y = 0
        self.ball_confidence = 0.0

        # =================================================
        # OBJECT MISSION
        # =================================================

        # Currently detected object
        # e.g. "tennis_ball", "traffic_cone", "hammer"
        self.object_class = None

        # LEFT, CENTRE, RIGHT, or None
        self.object_direction = None

        # =================================================
        # BALLOON MISSION
        # =================================================

        self.balloon_detected = False
        self.balloon_class = None
        self.balloon_x = 0
        self.balloon_y = 0
        self.balloon_width = 0
        self.balloon_height = 0
        self.balloon_confidence = 0.0

        # All currently detected balloons
        self.balloon_detections = []

        # Current balloon target
        self.balloon_target = "black_balloon"

        # WAITING, APPROACHING, STOPPED, COMPLETE, etc.
        self.balloon_status = "WAITING"

        # =================================================
        # ROBOT HEAD / POSE
        # =================================================

        self.camera_yaw = 90.0
        self.camera_pitch = 90.0

        # =================================================
        # TELEMETRY
        # =================================================

        self.wifi_connected = False
        self.battery = 0.0

        # Ultrasonic distance
        self.distance_cm = None
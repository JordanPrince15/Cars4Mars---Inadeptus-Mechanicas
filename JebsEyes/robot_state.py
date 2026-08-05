import threading


class RobotState:

    def __init__(self):

        self.lock = threading.Lock()

        # =================================================
        # VISION
        # =================================================

        self.frame = None

        self.ball_detected = False
        self.ball_x = 0
        self.ball_y = 0
        self.ball_confidence = 0.0

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
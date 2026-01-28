# rover_state.py
import threading

class RoverState:
    def __init__(self):
        self.lock = threading.Lock()

        # Vision
        self.frame = None
        self.ball_detected = False
        self.ball_x = 0
        self.ball_y = 0
        self.ball_confidence = 0.0

        # Robot pose (future)
        self.camera_yaw = 0.0
        self.camera_pitch = 0.0

        # Telemetry
        self.wifi_connected = False
        self.battery = 0.0
        # self.distance_cm = 0.0
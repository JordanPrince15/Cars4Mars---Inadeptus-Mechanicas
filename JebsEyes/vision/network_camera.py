# network_camera.py
import socket, struct, pickle
import cv2
import numpy as np

class NetworkCamera:
    def __init__(self, pi_ip="192.168.1.154", port=6000):
        self.pi_ip = pi_ip
        self.port = port
        self.sock = None
        self.data = b""
        self.payload_size = struct.calcsize(">I")
        self.frame = None
        self.distance = None

        self.connect()

    def connect(self):
        """Connect to the Pi server."""
        if self.sock:
            self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.pi_ip, self.port))
        print(f"[NetworkCamera] Connected to {self.pi_ip}:{self.port}")

    def read(self):
        """Read the next frame + distance from Pi."""
        while len(self.data) < self.payload_size:
            packet = self.sock.recv(4096)
            if not packet:
                raise ConnectionError("Disconnected from Pi")
            self.data += packet

        packed_msg_size = self.data[:self.payload_size]
        self.data = self.data[self.payload_size:]
        msg_size = struct.unpack(">I", packed_msg_size)[0]

        while len(self.data) < msg_size:
            packet = self.sock.recv(4096)
            if not packet:
                raise ConnectionError("Disconnected from Pi")
            self.data += packet

        msg_data = self.data[:msg_size]
        self.data = self.data[msg_size:]

        packet = pickle.loads(msg_data)
        self.frame = packet["frame"]
        self.distance = packet["distance"]

        return self.frame, self.distance

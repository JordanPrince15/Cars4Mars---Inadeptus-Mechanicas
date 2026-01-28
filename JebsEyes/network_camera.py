# # # # # # # network_camera.py
# # # # # # import socket, struct, pickle
# # # # # # import cv2
# # # # # # import numpy as np

# # # # # # class NetworkCamera:
# # # # # #     def __init__(self, pi_ip="192.168.1.154", port=6000):
# # # # # #         self.pi_ip = pi_ip
# # # # # #         self.port = port
# # # # # #         self.sock = None
# # # # # #         self.data = b""
# # # # # #         self.payload_size = struct.calcsize(">I")
# # # # # #         self.frame = None
# # # # # #         self.distance = None

# # # # # #         self.connect()

# # # # # #     def connect(self):
# # # # # #         """Connect to the Pi server."""
# # # # # #         if self.sock:
# # # # # #             self.sock.close()
# # # # # #         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # # # # #         self.sock.connect((self.pi_ip, self.port))
# # # # # #         print(f"[NetworkCamera] Connected to {self.pi_ip}:{self.port}")

# # # # # #     def read(self):
# # # # # #         """Read the next frame + distance from Pi."""
# # # # # #         while len(self.data) < self.payload_size:
# # # # # #             packet = self.sock.recv(4096)
# # # # # #             if not packet:
# # # # # #                 raise ConnectionError("Disconnected from Pi")
# # # # # #             self.data += packet

# # # # # #         packed_msg_size = self.data[:self.payload_size]
# # # # # #         self.data = self.data[self.payload_size:]
# # # # # #         msg_size = struct.unpack(">I", packed_msg_size)[0]

# # # # # #         while len(self.data) < msg_size:
# # # # # #             packet = self.sock.recv(4096)
# # # # # #             if not packet:
# # # # # #                 raise ConnectionError("Disconnected from Pi")
# # # # # #             self.data += packet

# # # # # #         msg_data = self.data[:msg_size]
# # # # # #         self.data = self.data[msg_size:]

# # # # # #         packet = pickle.loads(msg_data)
# # # # # #         self.frame = packet["frame"]
# # # # # #         self.distance = packet["distance"]

# # # # # #         return self.frame, self.distance


# # # # # # ------------------
# # # # # # Optimized version
# # # # # # ------------------

# # # # # import socket
# # # # # import struct
# # # # # import cv2
# # # # # import numpy as np


# # # # # class NetworkCamera:
# # # # #     def __init__(self, pi_ip, port):
# # # # #         self.pi_ip = pi_ip
# # # # #         self.port = port
# # # # #         self.sock = None
# # # # #         self.connect()

# # # # #     def connect(self):
# # # # #         if self.sock:
# # # # #             self.sock.close()

# # # # #         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # # # #         self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
# # # # #         self.sock.connect((self.pi_ip, self.port))
# # # # #         self.sock_file = self.sock.makefile("rb")
# # # # #         print("✅ Connected to network camera")

# # # # #     def read_exact(self, size):
# # # # #         data = b""
# # # # #         while len(data) < size:
# # # # #             chunk = self.sock_file.read(size - len(data))
# # # # #             if not chunk:
# # # # #                 raise ConnectionError("Socket closed")
# # # # #             data += chunk
# # # # #         return data

# # # # #     def read(self):
# # # # #         # Read header
# # # # #         header = self.read_exact(4)
# # # # #         img_size, distance = struct.unpack(">If", header)

# # # # #         # Read JPEG image
# # # # #         img_bytes = self.read_exact(img_size)

# # # # #         # Decode JPEG
# # # # #         img_array = np.frombuffer(img_bytes, dtype=np.uint8)
# # # # #         frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

# # # # #         if frame is None:
# # # # #             raise ValueError("Failed to decode image")

# # # # #         return frame, distance

# # # # # -------------------------------
# # # # # UPDATED VERSION 2
# # # # # -------------------------------

# # # # # network_camera.py
# # # # import socket
# # # # import struct
# # # # import pickle


# # # # class NetworkCamera:
# # # #     def __init__(self, pi_ip="192.168.1.154", port=6000):
# # # #         self.pi_ip = pi_ip
# # # #         self.port = port
# # # #         self.sock = None
# # # #         self.data = b""
# # # #         self.payload_size = struct.calcsize(">I")

# # # #         self.connect()

# # # #     def connect(self):
# # # #         if self.sock:
# # # #             self.sock.close()

# # # #         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # # #         # Remove TCP_NODELAY for now (or keep it, doesn't break)
# # # #         self.sock.connect((self.pi_ip, self.port))
# # # #         # Do NOT use makefile, use raw recv
# # # #         print("✅ Connected to network camera")

# # # #     def read(self):
# # # #         # First, read message size (blocking)
# # # #         packed_size = self.sock.recv(4)
# # # #         if not packed_size:
# # # #             raise ConnectionError("Disconnected")
# # # #         msg_size = struct.unpack(">I", packed_size)[0]

# # # #         # Read full payload
# # # #         data = b""
# # # #         while len(data) < msg_size:
# # # #             packet = self.sock.recv(4096)
# # # #             if not packet:
# # # #                 raise ConnectionError("Disconnected")
# # # #             data += packet

# # # #         packet = pickle.loads(data)
# # # #         return packet["frame"], packet["distance"]


# # #     # def read(self):
# # #     #     # Read message size
# # #     #     while len(self.data) < self.payload_size:
# # #     #         packet = self.sock.recv(4096)
# # #     #         if not packet:
# # #     #             raise ConnectionError("Disconnected from Pi")
# # #     #         self.data += packet

# # #     #     packed_size = self.data[:self.payload_size]
# # #     #     self.data = self.data[self.payload_size:]
# # #     #     msg_size = struct.unpack(">I", packed_size)[0]

# # #     #     # Read full payload
# # #     #     while len(self.data) < msg_size:
# # #     #         packet = self.sock.recv(4096)
# # #     #         if not packet:
# # #     #             raise ConnectionError("Disconnected from Pi")
# # #     #         self.data += packet

# # #     #     if len(self.data) < msg_size:
# # #     #         # Still not enough data, wait for more
# # #     #         return None, None

# # #     #     msg_data = self.data[:msg_size]
# # #     #     self.data = self.data[msg_size:]

# # #     #     if not msg_data:
# # #     #         return None, None

# # #     #     packet = pickle.loads(msg_data)

# # #     #     frame = packet["frame"]
# # #     #     distance = packet["distance"]

# # #     #     return frame, distance


# # #     # def read(self):
# # #     #     # Read message size
# # #     #     while len(self.data) < self.payload_size:
# # #     #         packet = self.sock.recv(4096)
# # #     #         if not packet:
# # #     #             raise ConnectionError("Disconnected from Pi")
# # #     #         self.data += packet

# # #     #     packed_size = self.data[:self.payload_size]
# # #     #     self.data = self.data[self.payload_size:]
# # #     #     msg_size = struct.unpack(">I", packed_size)[0]

# # #     #     # Read full payload
# # #     #     while len(self.data) < msg_size:
# # #     #         packet = self.sock.recv(4096)
# # #     #         if not packet:
# # #     #             raise ConnectionError("Disconnected from Pi")
# # #     #         self.data += packet

# # #     #     msg_data = self.data[:msg_size]
# # #     #     self.data = self.data[msg_size:]

# # #     #     packet = pickle.loads(msg_data)

# # #     #     frame = packet["frame"]
# # #     #     distance = packet["distance"]

# # #     #     return frame, distance

# # # import socket
# # # import struct
# # # import pickle

# # # class NetworkCamera:
# # #     def __init__(self, pi_ip="192.168.1.154", port=6000):
# # #         self.pi_ip = pi_ip
# # #         self.port = port
# # #         self.sock = None
# # #         self.connect()

# # #     def connect(self):
# # #         if self.sock:
# # #             self.sock.close()
# # #         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # #         self.sock.connect((self.pi_ip, self.port))
# # #         print(f"✅ Connected to network camera {self.pi_ip}:{self.port}")

# # #     def read(self):
# # #         # Blocking read for 4-byte header
# # #         packed_size = self.sock.recv(4)
# # #         if not packed_size:
# # #             raise ConnectionError("Disconnected from Pi")

# # #         msg_size = struct.unpack(">I", packed_size)[0]

# # #         # Read full payload
# # #         data = b""
# # #         while len(data) < msg_size:
# # #             packet = self.sock.recv(4096)
# # #             if not packet:
# # #                 raise ConnectionError("Disconnected from Pi")
# # #             data += packet

# # #         packet = pickle.loads(data)
# # #         return packet["frame"], packet["distance"]

# # import socket
# # import struct
# # import pickle
# # import cv2
# # import numpy as np

# # class NetworkCamera:
# #     def __init__(self, pi_ip="192.168.1.154", port=6000):
# #         self.pi_ip = pi_ip
# #         self.port = port
# #         self.sock = None
# #         self.connect()  # connect() will handle timeout

# #     def connect(self):
# #         if self.sock:
# #             self.sock.close()

# #         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# #         self.sock.settimeout(3.0)  # <-- set timeout here
# #         self.sock.connect((self.pi_ip, self.port))
# #         print(f"✅ Connected to network camera {self.pi_ip}:{self.port}")

# #     def read_exact(self, size):
# #         data = b""
# #         while len(data) < size:
# #             chunk = self.sock.recv(size - len(data))
# #             if not chunk:
# #                 raise ConnectionError("Socket closed")
# #             data += chunk
# #         return data

# #     # def read(self):
# #     #     # Read 4-byte header
# #     #     header = self.read_exact(4)
# #     #     payload_size = struct.unpack(">I", header)[0]

# #     #     # Read full payload
# #     #     payload = self.read_exact(payload_size)

# #     #     # Unpickle
# #     #     packet = pickle.loads(payload)

# #     #     # Decode JPEG back to frame
# #     #     jpg_bytes = packet["frame"]
# #     #     frame = cv2.imdecode(np.frombuffer(jpg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
# #     #     distance = packet["distance"]

# #     #     return frame, distance

# #     def read(self):
# #         print("[NetworkCamera] Waiting for header...")
# #         header = self.read_exact(4)
# #         print("[NetworkCamera] Got header")
# #         payload_size = struct.unpack(">I", header)[0]
# #         print(f"[NetworkCamera] Payload size: {payload_size}")

# #         payload = self.read_exact(payload_size)
# #         print("[NetworkCamera] Got full payload")

# #         packet = pickle.loads(payload)
# #         return packet["frame"], packet["distance"]


# import socket, struct, pickle
# import cv2
# import numpy as np

# class NetworkCamera:
#     def __init__(self, pi_ip="192.168.1.154", port=6000):
#         self.pi_ip = pi_ip
#         self.port = port
#         self.sock = None
#         self.connect()

#     def connect(self):
#         if self.sock:
#             self.sock.close()

#         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.sock.settimeout(2.0)
#         self.sock.connect((self.pi_ip, self.port))
#         print(f"✅ Connected to network camera {self.pi_ip}:{self.port}")

#     def read_exact(self, size):
#         data = b""
#         while len(data) < size:
#             chunk = self.sock.recv(size - len(data))
#             if not chunk:
#                 raise ConnectionError("Socket closed")
#             data += chunk
#         return data

#     def read(self):
#         try:
#             # Read header
#             header = self.read_exact(4)
#             if not header:
#                 return None, None

#             payload_size = struct.unpack("!I", header)[0]

#             # Sanity check
#             if payload_size <= 0 or payload_size > 2_000_000:
#                 print(f"[NetworkCamera] Invalid payload size: {payload_size}")
#                 self.flush_socket()
#                 return None, None

#             payload = self.read_exact(payload_size)
#             packet = pickle.loads(payload)

#             # HARD validation
#             if not isinstance(packet, dict):
#                 print("[NetworkCamera] Packet not dict")
#                 return None, None

#             if "jpg" not in packet:
#                 print(f"[NetworkCamera] Bad packet keys: {packet.keys()}")
#                 return None, None

#             jpg_bytes = packet["jpg"]
#             distance = packet.get("distance", None)

#             frame = cv2.imdecode(
#                 np.frombuffer(jpg_bytes, dtype=np.uint8),
#                 cv2.IMREAD_COLOR
#             )

#             return frame, distance

#         except (pickle.UnpicklingError, ConnectionResetError, TimeoutError) as e:
#             print(f"[NetworkCamera] Read error: {e}")
#             return None, None
#     def flush_socket(self):
#         try:
#             self.sock.setblocking(False)
#             while True:
#                 self.sock.recv(4096)
#         except:
#             pass
#         finally:
#             self.sock.setblocking(True)

import socket, struct, pickle
import cv2
import numpy as np

class NetworkCamera:
    def __init__(self, pi_ip="192.168.1.154", port=6000):
        self.pi_ip = pi_ip
        self.port = port
        self.sock = None
        self.connect()

    def connect(self):
        if self.sock:
            self.sock.close()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)
        self.sock.connect((self.pi_ip, self.port))
        print(f"✅ Connected to network camera {self.pi_ip}:{self.port}")

    def read_exact(self, size):
        data = b""
        while len(data) < size:
            chunk = self.sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Socket closed")
            data += chunk
        return data

    def read(self):
        try:
            header = self.read_exact(4)
            payload_size = struct.unpack(">I", header)[0]

            if payload_size <= 0 or payload_size > 2_000_000:
                raise ValueError("Bad payload size")

            payload = self.read_exact(payload_size)
            packet = pickle.loads(payload)

            jpg_bytes = packet["jpg"]
            distance = packet.get("distance", None)

            frame = cv2.imdecode(
                np.frombuffer(jpg_bytes, dtype=np.uint8),
                cv2.IMREAD_COLOR
            )

            return frame, distance

        except (TimeoutError, ConnectionError, pickle.UnpicklingError, ValueError) as e:
            print(f"[NetworkCamera] Read error: {e}")
            return None, None

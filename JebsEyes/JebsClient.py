# # import socket, struct, pickle
# # import cv2
# # import time

# # PI_IP = "192.168.1.154"  # change to your Pi IP
# # PORT = 6000

# # while True:
# #     try:
# #         print("Connecting to Pi...")
# #         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# #         s.connect((PI_IP, PORT))
# #         print("Connected!")

# #         data = b""
# #         payload_size = struct.calcsize(">I")

# #         while True:
# #             while len(data) < payload_size:
# #                 packet = s.recv(4096)
# #                 if not packet:
# #                     raise ConnectionError
# #                 data += packet

# #             packed_msg_size = data[:payload_size]
# #             data = data[payload_size:]
# #             msg_size = struct.unpack(">I", packed_msg_size)[0]

# #             while len(data) < msg_size:
# #                 packet = s.recv(4096)
# #                 if not packet:
# #                     raise ConnectionError
# #                 data += packet

# #             msg_data = data[:msg_size]
# #             data = data[msg_size:]

# #             packet = pickle.loads(msg_data)
# #             frame = packet["frame"]
# #             distance = packet["distance"]

# #             cv2.imshow("Video Stream", frame)
# #             print(f"Distance: {distance:.2f} cm")

# #             if cv2.waitKey(1) & 0xFF == ord('q'):
# #                 raise KeyboardInterrupt

# #     except (ConnectionError, OSError):
# #         print("Lost connection. Retrying in 2 seconds...")
# #         cv2.destroyAllWindows()
# #         time.sleep(2)
# #     except KeyboardInterrupt:
# #         break

# # cv2.destroyAllWindows()

# import cv2
# from network_camera import NetworkCamera

# PI_IP = "192.168.1.154"  # change to your Pi IP
# PORT = 6000

# while True:
#     try:
#         net_cam = NetworkCamera(pi_ip=PI_IP, port=PORT)
#         while True:
#             frame, distance = net_cam.read()
#             cv2.imshow("Video Stream", frame)
#             print(f"Distance: {distance:.2f} cm")

#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 raise KeyboardInterrupt

#     except (ConnectionError, OSError):
#         print("Lost connection. Retrying in 2 seconds...")
#         cv2.destroyAllWindows()
#         import time; time.sleep(2)
#     except KeyboardInterrupt:
#         break

# cv2.destroyAllWindows()


import socket
import struct
import pickle
import cv2
import time
import numpy as np

PI_IP = "192.168.1.154"
PORT = 6000

while True:
    try:
        print("Connecting to Pi...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((PI_IP, PORT))
        print("✅ Connected!")

        data = b""
        payload_size = struct.calcsize(">I")

        while True:
            # Read header
            while len(data) < payload_size:
                packet = sock.recv(4096)
                if not packet:
                    raise ConnectionError
                data += packet

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">I", packed_msg_size)[0]

            # Read full payload
            while len(data) < msg_size:
                packet = sock.recv(4096)
                if not packet:
                    raise ConnectionError
                data += packet

            msg_data = data[:msg_size]
            data = data[msg_size:]

            # Decode frame
            packet = pickle.loads(msg_data)
            frame = cv2.imdecode(
                np.frombuffer(packet["jpg"], dtype=np.uint8),
                cv2.IMREAD_COLOR
            )
            distance = packet.get("distance", -1.0)

            # Display
            cv2.imshow("Rover Camera", frame)
            print(f"Distance: {distance:.2f} cm")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                raise KeyboardInterrupt

    except (ConnectionError, OSError):
        print("Lost connection. Retrying in 2 seconds...")
        cv2.destroyAllWindows()
        time.sleep(2)
    except KeyboardInterrupt:
        break

cv2.destroyAllWindows()

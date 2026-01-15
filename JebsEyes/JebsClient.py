import socket, struct, pickle
import cv2
import time

PI_IP = "192.168.1.154"  # change to your Pi IP
PORT = 6000

while True:
    try:
        print("Connecting to Pi...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((PI_IP, PORT))
        print("Connected!")

        data = b""
        payload_size = struct.calcsize(">I")

        while True:
            while len(data) < payload_size:
                packet = s.recv(4096)
                if not packet:
                    raise ConnectionError
                data += packet

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">I", packed_msg_size)[0]

            while len(data) < msg_size:
                packet = s.recv(4096)
                if not packet:
                    raise ConnectionError
                data += packet

            msg_data = data[:msg_size]
            data = data[msg_size:]

            packet = pickle.loads(msg_data)
            frame = packet["frame"]
            distance = packet["distance"]

            cv2.imshow("Video Stream", frame)
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

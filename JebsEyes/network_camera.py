import cv2


class NetworkCamera:

    def __init__(
        self,
        stream_url="http://192.168.0.142:5000/video"
    ):

        self.stream_url = stream_url
        self.cap = None

        self.connect()


    def connect(self):

        # Close existing connection
        if self.cap is not None:

            try:
                self.cap.release()

            except Exception:
                pass

        print(
            f"Connecting to Jeb's camera: "
            f"{self.stream_url}"
        )

        self.cap = cv2.VideoCapture(
            self.stream_url
        )

        if not self.cap.isOpened():

            self.cap = None

            raise ConnectionError(
                "Could not connect to Jeb's camera stream."
            )

        print("Connected to Jeb's camera!")


    def read(self):

        if self.cap is None:

            raise ConnectionError(
                "Camera is not connected."
            )


        ret, frame = self.cap.read()


        if not ret or frame is None:

            print(
                "[NetworkCamera] "
                "Failed to receive frame."
            )

            self.cap.release()
            self.cap = None

            raise ConnectionError(
                "Camera stream stopped."
            )


        # Jeb's camera is mounted upside down
        frame = cv2.flip(
            frame,
            -1
        )


        # The old system returned a distance value.
        # Our camera stream currently does not provide one.
        distance = None


        return frame, distance


    def release(self):

        if self.cap is not None:

            self.cap.release()

            self.cap = None
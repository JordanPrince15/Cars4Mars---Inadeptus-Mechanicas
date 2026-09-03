import cv2

class CameraManager:
    def __init__(self):
        self.cap = None
        self.index = None

    def connect(self):
        for index in [1, 0, 2, 3]:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    self.cap = cap
                    self.index = index
                    return True
                cap.release()
        return False

    def read(self):
        if self.cap:
            return self.cap.read()
        return False, None

    def release(self):
        if self.cap:
            self.cap.release()
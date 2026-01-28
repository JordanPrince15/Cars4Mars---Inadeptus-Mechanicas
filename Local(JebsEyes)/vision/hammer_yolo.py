from ultralytics import YOLO

class HammerDetector:
    def __init__(self, model_path=r"D:\Trained-dataset\train2\weights\best.pt", conf=0.5):
        """
        Initialize the hammer YOLO detector.
        Args:
            model_path: path to your trained YOLOv8 model (.pt)
            conf: confidence threshold for detections
        """
        self.model = YOLO(model_path)
        self.conf = conf

    def detect(self, frame):
        """
        Detect a hammer in a single frame.
        Args:
            frame: BGR image (numpy array)
        Returns:
            dict with x, y, size, confidence OR None if no hammer detected
        """
        results = self.model.predict(source=frame, conf=self.conf, verbose=False)

        if results and results[0].boxes:
            # Take the first detection
            box = results[0].boxes.xyxy[0]  # [x1, y1, x2, y2]
            confidence = results[0].boxes.conf[0].item()

            x1, y1, x2, y2 = map(int, box)
            x = (x1 + x2) // 2
            y = (y1 + y2) // 2
            size = max(x2 - x1, y2 - y1) // 2  # approximate radius

            return {"x": x, "y": y, "size": size, "confidence": confidence}

        return None

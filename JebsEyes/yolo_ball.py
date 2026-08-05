import cv2
import numpy as np
import warnings

# We try to import the real engine. If you haven't installed it yet, run: pip install ultralytics
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False
    warnings.warn("⚠️ ultralytics package not installed. YOLO detection is currently mocking dummy data!")

class TennisBallDetector:
    def __init__(self, model_path="yolov8n.pt"):
        """
        Initialize the real YOLO target detector.
        Downloads / loads standard lightweight nano weights if no custom model is found.
        """
        if HAS_YOLO:
            # yolov8n detects "sports ball" out of the box (Class ID 32 in standard COCO dataset)
            self.model = YOLO(model_path)
            self.target_class_id = 32 
        else:
            self.model = None

    def detect(self, frame):
        """
        Run actual deep learning inference on the frame to find the ball.
        """
        if frame is None:
            return None

        if not HAS_YOLO:
            # Fallback placeholder so your code runs while you configure your packages
            return None

        # Run inference with a low threshold for responsiveness
        results = self.model(frame, verbose=False, conf=0.35)[0]
        
        best_box = None
        max_conf = 0.0

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            # Filter specifically for the sports ball tracking token
            if cls_id == self.target_class_id:
                if conf > max_conf:
                    max_conf = conf
                    best_box = box

        if best_box is not None:
            # Extract standard bounding box coordinates
            xyxy = best_box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = xyxy
            
            # Convert to target payload structures
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            estimated_radius = int(max(x2 - x1, y2 - y1) / 2)

            return {
                "x": center_x,
                "y": center_y,
                "size": estimated_radius,
                "confidence": max_conf
            }

        return None
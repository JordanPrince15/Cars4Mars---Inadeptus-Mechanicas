import math

def fuse_detections(hsv_det, yolo_det, proximity_threshold=80):
    """
    Fuse HSV and YOLO detections for a tennis ball using a spatial proximity check.
    Returns one combined detection, the higher confidence tracker, or None.
    """
    if hsv_det and yolo_det:
        # Calculate Euclidean distance between the two bounding box centers
        dx = hsv_det["x"] - yolo_det["x"]
        dy = hsv_det["y"] - yolo_det["y"]
        distance = math.sqrt(dx*dx + dy*dy)

        # If they are close enough, fuse them together safely
        if distance <= proximity_threshold:
            total_conf = hsv_det["confidence"] + yolo_det["confidence"]

            x = int((hsv_det["x"] * hsv_det["confidence"] + yolo_det["x"] * yolo_det["confidence"]) / total_conf)
            y = int((hsv_det["y"] * hsv_det["confidence"] + yolo_det["y"] * yolo_det["confidence"]) / total_conf)
            size = max(hsv_det["size"], yolo_det["size"])
            confidence = min(1.0, max(hsv_det["confidence"], yolo_det["confidence"]))

            return {
                "name": "tennis_ball",
                "x": x,
                "y": y,
                "size": size,
                "confidence": confidence
            }
        
        # If they are pointing to different spots, trust the heavier YOLO model
        return yolo_det

    if hsv_det:
        return hsv_det

    if yolo_det:
        return yolo_det

    return None
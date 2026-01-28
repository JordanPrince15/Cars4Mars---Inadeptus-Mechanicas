def fuse_detections(hsv_det, yolo_det):
    """
    Fuse HSV and YOLO detections for a tennis ball.
    Returns one detection or None.
    """

    if hsv_det and yolo_det:
        # Confidence-weighted average
        total_conf = hsv_det["confidence"] + yolo_det["confidence"]

        x = int(
            (hsv_det["x"] * hsv_det["confidence"] +
             yolo_det["x"] * yolo_det["confidence"]) / total_conf
        )
        y = int(
            (hsv_det["y"] * hsv_det["confidence"] +
             yolo_det["y"] * yolo_det["confidence"]) / total_conf
        )

        size = max(hsv_det["size"], yolo_det["size"])

        confidence = max(hsv_det["confidence"], yolo_det["confidence"])

        return {
            "name": "tennis_ball",
            "x": x,
            "y": y,
            "size": size,
            "confidence": confidence
        }

    elif hsv_det:
        return hsv_det

    elif yolo_det:
        return yolo_det

    return None

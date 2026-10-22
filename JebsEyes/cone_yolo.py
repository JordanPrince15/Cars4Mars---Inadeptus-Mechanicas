from pathlib import Path

from ultralytics import YOLO


def _default_cone_model_path():
    candidates = [
        Path(r"D:\Trained-dataset\traffic cone dataset\runs\detect\train\weights\best.pt"),
        Path(__file__).resolve().parents[2] / "Trained-dataset" / "traffic cone dataset" / "runs" / "detect" / "train" / "weights" / "best.pt",
    ]

    for path in candidates:
        if path.exists():
            return str(path)

    return str(candidates[0])


class ConeDetector:

    def __init__(
        self,
        model_path=None,
        conf=0.5
    ):
        """
        Initialize the traffic cone YOLO detector.

        Args:
            model_path: Path to the trained YOLO model.
            conf: Minimum confidence threshold.
        """

        if model_path is None:
            model_path = _default_cone_model_path()

        self.model = YOLO(model_path)
        self.conf = conf

        print("✓ Cone detector initialized.")
        print(f"  Model: {model_path}")
        print(f"  Confidence threshold: {conf}")

    def detect(self, frame):
        """
        Detect traffic cones in a single frame.

        Args:
            frame: BGR image from OpenCV.

        Returns:
            List of cone detection dictionaries.
        """

        results = self.model.predict(
            source=frame,
            conf=self.conf,
            verbose=False
        )

        detections = []

        if not results:
            return detections

        result = results[0]

        if result.boxes is None:
            return detections

        for box, confidence in zip(
            result.boxes.xyxy,
            result.boxes.conf
        ):

            x1, y1, x2, y2 = map(
                int,
                box.tolist()
            )

            confidence = float(
                confidence.item()
            )

            # Centre coordinates
            x = (x1 + x2) // 2
            y = (y1 + y2) // 2

            # Bounding-box dimensions
            width = x2 - x1
            height = y2 - y1

            detections.append({
                "class": "traffic_cone",
                "confidence": confidence,
                "x": x,
                "y": y,
                "width": width,
                "height": height
            })

        return detections


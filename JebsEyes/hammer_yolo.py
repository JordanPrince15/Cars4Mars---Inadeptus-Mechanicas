from pathlib import Path

from ultralytics import YOLO


def _default_hammer_model_path():
    # Prefer the finished 50-epoch hammer run (train3).
    # train2 was stopped after 6 epochs and misses most FPV views.
    candidates = [
        Path(__file__).resolve().parents[2] / "Trained-dataset" / "train3" / "weights" / "best.pt",
        Path(r"D:\Trained-dataset\train3\weights\best.pt"),
        Path(r"D:\Trained-dataset\train2\weights\best.pt"),
        Path(__file__).resolve().parents[2] / "Trained-dataset" / "train2" / "weights" / "best.pt",
        Path(__file__).resolve().parents[1] / "train2" / "weights" / "best.pt",
    ]

    for path in candidates:
        if path.exists():
            return str(path)

    return str(candidates[0])


class HammerDetector:

    def __init__(
        self,
        model_path=None,
        conf=0.25
    ):
        """
        Initialize the hammer YOLO detector.

        Args:
            model_path: Path to the trained YOLO model.
            conf: Minimum confidence required for a detection.
        """

        if model_path is None:
            model_path = _default_hammer_model_path()

        self.model = YOLO(model_path)
        self.conf = conf

        print("✓ Hammer detector initialized.")
        print(f"  Model: {model_path}")
        print(f"  Confidence threshold: {conf}")

    def detect(self, frame):
        """
        Detect hammers in a single frame.

        Args:
            frame: BGR image from OpenCV.

        Returns:
            List of detection dictionaries.

        Each detection contains:
            class
            confidence
            x
            y
            width
            height
        """

        results = self.model.predict(
            source=frame,
            conf=self.conf,
            imgsz=640,
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

            x = (x1 + x2) // 2
            y = (y1 + y2) // 2

            width = x2 - x1
            height = y2 - y1

            detections.append({
                "class": "hammer",
                "confidence": confidence,
                "x": x,
                "y": y,
                "width": width,
                "height": height
            })

        return detections


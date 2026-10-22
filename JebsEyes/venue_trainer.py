import json
import re
import shutil
import threading
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


def slug_class_name(name):
    slug = re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower())
    slug = slug.strip("_")
    return slug or "object"


def _clamp_box(box, width, height):
    x1, y1, x2, y2 = box
    x1 = max(0.0, min(float(x1), float(width)))
    y1 = max(0.0, min(float(y1), float(height)))
    x2 = max(0.0, min(float(x2), float(width)))
    y2 = max(0.0, min(float(y2), float(height)))

    left = min(x1, x2)
    top = min(y1, y2)
    right = max(x1, x2)
    bottom = max(y1, y2)

    if right - left < 8 or bottom - top < 8:
        raise ValueError("Bounding box is too small.")

    return [left, top, right, bottom]


class VenueTrainer:
    """
    Venue-day labelling and YOLO fine-tune for a single object class.
    Overfitting on a handful of camera shots is intentional.
    """

    def __init__(self, root_dir, object_mission=None, state=None):
        self.root = Path(root_dir)
        self.images_dir = self.root / "images"
        self.labels_dir = self.root / "labels"
        self.yolo_dir = self.root / "yolo"
        self.runs_dir = self.root / "runs"
        self.session_path = self.root / "session.json"
        self.object_mission = object_mission
        self.state = state

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

        self.lock = threading.Lock()
        self.session = self._load_session()
        self.job = {
            "status": "idle",
            "message": "No training job yet.",
            "logs": [],
            "class_name": None,
            "epochs": 0,
            "weights_path": None,
            "started_at": None,
            "finished_at": None,
            "applied": None
        }
        self._train_thread = None

    def refresh_detection(self):
        """
        Turn live object detection off while the Train page
        is open or a fine-tune job is running.
        """

        if self.state is None:
            return False

        with self.lock:
            training = self.job.get("status") == "running"

        with self.state.lock:
            on_train_page = self.state.ui_mode == "train"
            self.state.detection_enabled = (
                (not on_train_page) and (not training)
            )
            return self.state.detection_enabled

    def _load_session(self):
        if self.session_path.exists():
            try:
                data = json.loads(
                    self.session_path.read_text(encoding="utf-8")
                )
                data.setdefault("class_name", "hammer")
                data.setdefault("images", {})
                return data
            except Exception:
                pass

        return {
            "class_name": "hammer",
            "images": {}
        }

    def _save_session(self):
        self.session_path.write_text(
            json.dumps(self.session, indent=2),
            encoding="utf-8"
        )

    def _public_image(self, image_id, record):
        return {
            "id": image_id,
            "url": f"/venue/images/{record['filename']}",
            "width": record["width"],
            "height": record["height"],
            "box": record.get("box"),
            "labelled": record.get("box") is not None
        }

    def get_session(self):
        with self.lock:
            images = [
                self._public_image(image_id, record)
                for image_id, record in self.session["images"].items()
            ]

            labelled = sum(1 for item in images if item["labelled"])
            job = dict(self.job)
            job["logs"] = list(self.job.get("logs", []))

            return {
                "class_name": self.session["class_name"],
                "images": images,
                "counts": {
                    "total": len(images),
                    "labelled": labelled
                },
                "job": job
            }

    def set_class_name(self, class_name):
        name = (class_name or "").strip()
        if not name:
            raise ValueError("Class name cannot be empty.")

        with self.lock:
            self.session["class_name"] = name
            self._save_session()
            return self.session["class_name"]

    def add_image_from_bytes(self, data, original_name="upload.jpg"):
        array = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError(
                f"Could not read image: {original_name}"
            )

        image_id = uuid.uuid4().hex[:12]
        filename = f"{image_id}.jpg"
        path = self.images_dir / filename

        ok = cv2.imwrite(str(path), image)
        if not ok:
            raise ValueError("Could not save uploaded image.")

        height, width = image.shape[:2]
        record = {
            "filename": filename,
            "original_name": original_name,
            "width": int(width),
            "height": int(height),
            "box": None
        }

        with self.lock:
            self.session["images"][image_id] = record
            self._save_session()
            return self._public_image(image_id, record)

    def add_image_from_frame(self, frame):
        if frame is None:
            raise ValueError("No live camera frame yet.")

        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            raise ValueError("Could not encode live frame.")

        return self.add_image_from_bytes(
            buffer.tobytes(),
            original_name="live-frame.jpg"
        )

    def set_box(self, image_id, box):
        with self.lock:
            record = self.session["images"].get(image_id)
            if record is None:
                raise KeyError("Image not found.")

            normalised = _clamp_box(
                box,
                record["width"],
                record["height"]
            )
            record["box"] = normalised
            self._write_label(image_id, record)
            self._save_session()
            return self._public_image(image_id, record)

    def delete_image(self, image_id):
        with self.lock:
            record = self.session["images"].pop(image_id, None)
            if record is None:
                raise KeyError("Image not found.")

            image_path = self.images_dir / record["filename"]
            label_path = self.labels_dir / f"{image_id}.txt"

            if image_path.exists():
                image_path.unlink()
            if label_path.exists():
                label_path.unlink()

            self._save_session()

    def _write_label(self, image_id, record):
        box = record.get("box")
        if not box:
            return

        x1, y1, x2, y2 = box
        width = record["width"]
        height = record["height"]

        x_center = ((x1 + x2) / 2.0) / width
        y_center = ((y1 + y2) / 2.0) / height
        box_w = abs(x2 - x1) / width
        box_h = abs(y2 - y1) / height

        label_path = self.labels_dir / f"{image_id}.txt"
        label_path.write_text(
            f"0 {x_center:.6f} {y_center:.6f} {box_w:.6f} {box_h:.6f}\n",
            encoding="utf-8"
        )

    def _log(self, message):
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {message}"
        with self.lock:
            self.job["logs"].append(line)
            self.job["logs"] = self.job["logs"][-200:]
            self.job["message"] = message
        print(f"[TRAIN] {message}")

    def start_train(self, class_name=None, epochs=15):
        with self.lock:
            if self.job["status"] == "running":
                raise RuntimeError("A training job is already running.")

            if class_name:
                self.session["class_name"] = class_name.strip()
                self._save_session()

            name = self.session["class_name"].strip()
            if not name:
                raise ValueError("Set a class name before training.")

            labelled = [
                (image_id, record)
                for image_id, record in self.session["images"].items()
                if record.get("box")
            ]

            if not labelled:
                raise ValueError(
                    "Draw a bounding box on at least one image first."
                )

            epochs = int(epochs)
            if epochs < 1 or epochs > 80:
                raise ValueError("Epochs must be between 1 and 80.")

            self.job = {
                "status": "running",
                "message": "Starting fine-tune...",
                "logs": [],
                "class_name": name,
                "epochs": epochs,
                "weights_path": None,
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "finished_at": None,
                "applied": None
            }

            self._train_thread = threading.Thread(
                target=self._run_train,
                args=(name, labelled, epochs),
                daemon=True
            )
            self._train_thread.start()

        self.refresh_detection()
        return dict(self.job)

    def _run_train(self, class_name, labelled, epochs):
        try:
            self._log(
                f"Fine-tuning '{class_name}' on {len(labelled)} image(s), "
                f"{epochs} epoch(s)."
            )
            data_yaml = self._build_yolo_dataset(class_name, labelled)
            base_model = self._base_model_path(class_name)
            self._log(f"Starting from {base_model}")

            from ultralytics import YOLO

            try:
                import torch
                device = 0 if torch.cuda.is_available() else "cpu"
            except Exception:
                device = "cpu"

            self._log(f"Device: {device}")

            model = YOLO(base_model)

            def on_epoch_end(trainer):
                current = trainer.epoch + 1
                total = trainer.epochs
                self._log(f"Epoch {current}/{total} complete")

            model.add_callback("on_train_epoch_end", on_epoch_end)

            results = model.train(
                data=str(data_yaml),
                epochs=epochs,
                imgsz=640,
                batch=min(4, max(1, len(labelled))),
                device=device,
                project=str(self.runs_dir),
                name="venue",
                exist_ok=True,
                pretrained=True,
                workers=0,
                verbose=True,
                patience=0,
                val=True
            )

            weights_path = Path(results.save_dir) / "weights" / "best.pt"
            if not weights_path.exists():
                raise FileNotFoundError(
                    "Training finished but best.pt was not created."
                )

            applied = None
            if self.object_mission is not None:
                applied = self.object_mission.load_venue_weights(
                    class_name,
                    str(weights_path)
                )

            with self.lock:
                self.job["status"] = "done"
                self.job["weights_path"] = str(weights_path)
                self.job["applied"] = applied
                self.job["finished_at"] = datetime.now().isoformat(
                    timespec="seconds"
                )

            self._log(f"Saved weights: {weights_path}")
            if applied:
                self._log(applied)
            self._log("Fine-tune complete. Switch to Live Detect to check it.")

        except Exception as error:
            with self.lock:
                self.job["status"] = "error"
                self.job["finished_at"] = datetime.now().isoformat(
                    timespec="seconds"
                )
            self._log(f"Training failed: {error}")

        finally:
            self.refresh_detection()

    def _build_yolo_dataset(self, class_name, labelled):
        if self.yolo_dir.exists():
            shutil.rmtree(self.yolo_dir)

        train_images = self.yolo_dir / "images" / "train"
        train_labels = self.yolo_dir / "labels" / "train"
        val_images = self.yolo_dir / "images" / "val"
        val_labels = self.yolo_dir / "labels" / "val"

        for folder in (train_images, train_labels, val_images, val_labels):
            folder.mkdir(parents=True, exist_ok=True)

        for image_id, record in labelled:
            source_image = self.images_dir / record["filename"]
            source_label = self.labels_dir / f"{image_id}.txt"

            if not source_label.exists():
                self._write_label(image_id, record)

            shutil.copy2(source_image, train_images / record["filename"])
            shutil.copy2(source_label, train_labels / f"{image_id}.txt")
            shutil.copy2(source_image, val_images / record["filename"])
            shutil.copy2(source_label, val_labels / f"{image_id}.txt")

        data_yaml = self.yolo_dir / "data.yaml"
        names = slug_class_name(class_name)
        yaml_path = self.yolo_dir.resolve().as_posix()
        data_yaml.write_text(
            (
                f"path: {yaml_path}\n"
                "train: images/train\n"
                "val: images/val\n"
                "nc: 1\n"
                f"names: ['{names}']\n"
            ),
            encoding="utf-8"
        )
        return data_yaml

    def _base_model_path(self, class_name):
        name = slug_class_name(class_name)

        if name == "hammer":
            from JebsEyes.hammer_yolo import _default_hammer_model_path
            path = Path(_default_hammer_model_path())
            if path.exists():
                return str(path)

        if name in ("cone", "traffic_cone"):
            from JebsEyes.cone_yolo import _default_cone_model_path
            path = Path(_default_cone_model_path())
            if path.exists():
                return str(path)

        return "yolov8n.pt"

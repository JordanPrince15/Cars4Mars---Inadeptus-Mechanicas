import asyncio
import socket
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    Response,
    StreamingResponse
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from JebsEyes.venue_trainer import VenueTrainer


WEB_HOST = "0.0.0.0"
WEB_PORT = 8000
UI_DIR = Path(__file__).resolve().parent
HTML_PATH = UI_DIR / "web_page.html"


class BoxBody(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class ClassBody(BaseModel):
    class_name: str


class TrainBody(BaseModel):
    class_name: str | None = None
    epochs: int = Field(default=15, ge=1, le=80)


class AnnotatedFrameBroker:
    """
    Holds the latest annotated JPEG and writes screenshots to disk.
    """

    def __init__(
        self,
        save_dir,
        archive_interval=1.0,
        max_archives=200
    ):
        self.save_dir = Path(save_dir)
        self.archive_dir = self.save_dir / "annotated"
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self.archive_interval = archive_interval
        self.max_archives = max_archives

        self.lock = threading.Lock()
        self.jpeg = None
        self.last_archive = 0.0
        self.last_archive_name = None
        self.frame_count = 0
        self.archiving = False

    def set_archiving(self, enabled):
        with self.lock:
            self.archiving = bool(enabled)

            if self.archiving:
                # Save the next frame immediately after Start.
                self.last_archive = 0.0

        return self.archiving

    def is_archiving(self):
        with self.lock:
            return self.archiving

    def publish(self, frame):
        ok, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        )

        if not ok:
            return

        jpeg = buffer.tobytes()

        with self.lock:
            self.jpeg = jpeg
            self.frame_count += 1
            archiving = self.archiving

        latest_path = self.save_dir / "latest.jpg"
        latest_path.write_bytes(jpeg)

        if not archiving:
            return

        now = time.monotonic()

        if now - self.last_archive >= self.archive_interval:
            self._archive(jpeg)

    def save_now(self):
        with self.lock:
            jpeg = self.jpeg

        if jpeg is None:
            return None

        return self._archive(jpeg)

    def _archive(self, jpeg):
        stamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S-%f"
        )[:-3]

        filename = f"{stamp}.jpg"
        path = self.archive_dir / filename
        path.write_bytes(jpeg)

        self.last_archive = time.monotonic()
        self.last_archive_name = filename

        archives = sorted(self.archive_dir.glob("*.jpg"))

        for old in archives[:-self.max_archives]:
            try:
                old.unlink()
            except Exception:
                pass

        return filename

    def get_jpeg(self):
        with self.lock:
            return self.jpeg

    def list_archives(self, limit=24):
        files = sorted(
            self.archive_dir.glob("*.jpg"),
            reverse=True
        )

        return [
            {
                "name": path.name,
                "url": f"/captures/annotated/{path.name}"
            }
            for path in files[:limit]
        ]


def local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        sock.close()


def viewer_urls():
    return {
        "local": f"http://127.0.0.1:{WEB_PORT}",
        "lan": f"http://{local_ip()}:{WEB_PORT}"
    }


def render_page(start="live"):
    html = HTML_PATH.read_text(encoding="utf-8")
    return html.replace(
        'data-start="live"',
        f'data-start="{start}"',
        1
    )


def json_error(message, status_code=400):
    return JSONResponse(
        {"error": message},
        status_code=status_code
    )


def create_app(broker, state, camera, mission_controller=None):
    app = FastAPI(title="Jeb Annotated Feed")

    object_mission = None
    if mission_controller is not None:
        object_mission = getattr(
            mission_controller,
            "object_mission",
            None
        )

    trainer = VenueTrainer(
        Path(broker.save_dir) / "venue-train",
        object_mission=object_mission,
        state=state
    )

    @app.get("/", response_class=HTMLResponse)
    def index():
        return render_page("live")

    @app.get("/train", response_class=HTMLResponse)
    def train_page():
        return render_page("train")

    @app.get("/api/latest.jpg")
    def latest_jpg():
        jpeg = broker.get_jpeg()

        if jpeg is None:
            return Response(
                status_code=204,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate"
                }
            )

        return Response(
            content=jpeg,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )

    @app.get("/api/stream")
    async def stream():
        async def generate():
            while True:
                jpeg = broker.get_jpeg()

                if jpeg is not None:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n"
                        + jpeg
                        + b"\r\n"
                    )

                await asyncio.sleep(0.05)

        return StreamingResponse(
            generate(),
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Connection": "keep-alive"
            }
        )

    @app.get("/api/status")
    def status():
        with state.lock:
            payload = {
                "control_mode": state.control_mode,
                "mission": state.mission,
                "ball_detected": state.ball_detected,
                "object_class": state.object_class,
                "object_direction": state.object_direction,
                "ball_confidence": state.ball_confidence,
                "balloon_detected": state.balloon_detected,
                "balloon_class": state.balloon_class,
                "source": getattr(camera, "active_mode", None),
                "ui_mode": getattr(state, "ui_mode", "live"),
                "detection_enabled": getattr(
                    state,
                    "detection_enabled",
                    True
                ),
                "monitor": None,
                "last_archive": broker.last_archive_name,
                "frame_count": broker.frame_count,
                "archiving": broker.is_archiving()
            }

        if (
            getattr(camera, "active_mode", None) == "screen"
            and hasattr(camera.camera, "monitor_index")
        ):
            payload["monitor"] = camera.camera.monitor_index

        return JSONResponse(payload)

    @app.post("/api/ui-mode/{mode}")
    def set_ui_mode(mode: str):
        mode = mode.lower()

        if mode not in ("live", "train"):
            return json_error("Mode must be live or train.")

        with state.lock:
            state.ui_mode = mode

        detection_enabled = trainer.refresh_detection()

        return JSONResponse({
            "ui_mode": mode,
            "detection_enabled": detection_enabled
        })

    @app.get("/api/captures")
    def captures():
        return JSONResponse(broker.list_archives())

    @app.post("/api/archive/start")
    def start_archive():
        return JSONResponse({
            "ok": True,
            "archiving": broker.set_archiving(True)
        })

    @app.post("/api/archive/stop")
    def stop_archive():
        return JSONResponse({
            "ok": True,
            "archiving": broker.set_archiving(False)
        })

    @app.post("/api/save")
    def save():
        filename = broker.save_now()

        if filename is None:
            return JSONResponse(
                {"saved": False, "error": "No annotated frame yet."},
                status_code=409
            )

        return JSONResponse({
            "saved": True,
            "name": filename,
            "url": f"/captures/annotated/{filename}"
        })

    @app.get("/api/monitors")
    def monitors():
        if (
            getattr(camera, "active_mode", None) != "screen"
            or not hasattr(camera.camera, "list_monitors")
        ):
            return JSONResponse([])

        return JSONResponse(camera.camera.list_monitors())

    @app.post("/api/monitor/{monitor_id}")
    def set_monitor(monitor_id: int):
        if (
            getattr(camera, "active_mode", None) != "screen"
            or not hasattr(camera.camera, "set_monitor")
        ):
            return JSONResponse(
                {"ok": False, "error": "Screen capture is not active."},
                status_code=409
            )

        camera.camera.set_monitor(monitor_id)

        return JSONResponse({
            "ok": True,
            "monitor": camera.camera.monitor_index
        })

    @app.get("/api/train/session")
    def train_session():
        return JSONResponse(trainer.get_session())

    @app.put("/api/train/class")
    def train_class(payload: ClassBody):
        try:
            class_name = trainer.set_class_name(payload.class_name)
            return JSONResponse({"class_name": class_name})
        except ValueError as error:
            return json_error(str(error))

    @app.post("/api/train/images")
    async def upload_images(files: list[UploadFile] = File(...)):
        added = []

        try:
            for upload in files:
                data = await upload.read()
                added.append(
                    trainer.add_image_from_bytes(
                        data,
                        upload.filename or "upload.jpg"
                    )
                )
        except ValueError as error:
            return json_error(str(error))

        return JSONResponse({"images": added})

    @app.post("/api/train/grab-live")
    def grab_live():
        with state.lock:
            frame = getattr(state, "raw_frame", None)
            if frame is not None:
                frame = frame.copy()

        if frame is None:
            return json_error("No live camera frame yet.", 409)

        try:
            return JSONResponse(trainer.add_image_from_frame(frame))
        except ValueError as error:
            return json_error(str(error))

    @app.put("/api/train/images/{image_id}/box")
    def set_box(image_id: str, payload: BoxBody):
        try:
            return JSONResponse(
                trainer.set_box(
                    image_id,
                    [payload.x1, payload.y1, payload.x2, payload.y2]
                )
            )
        except KeyError:
            return json_error("Image not found.", 404)
        except ValueError as error:
            return json_error(str(error))

    @app.delete("/api/train/images/{image_id}")
    def delete_image(image_id: str):
        try:
            trainer.delete_image(image_id)
            return JSONResponse({"ok": True})
        except KeyError:
            return json_error("Image not found.", 404)

    @app.post("/api/train/start")
    def start_train(payload: TrainBody):
        try:
            return JSONResponse(
                trainer.start_train(
                    class_name=payload.class_name,
                    epochs=payload.epochs
                )
            )
        except (ValueError, RuntimeError) as error:
            return json_error(str(error))

    app.mount(
        "/captures",
        StaticFiles(directory=str(broker.save_dir)),
        name="captures"
    )

    app.mount(
        "/venue",
        StaticFiles(directory=str(trainer.root)),
        name="venue"
    )

    return app


def start_web_viewer(broker, state, camera, mission_controller=None):
    import uvicorn

    app = create_app(
        broker,
        state,
        camera,
        mission_controller
    )
    config = uvicorn.Config(
        app,
        host=WEB_HOST,
        port=WEB_PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(
        target=server.run,
        daemon=True
    )
    thread.start()

    urls = viewer_urls()

    print()
    print("==============================")
    print("     ANNOTATED WEB FEED")
    print("==============================")
    print(f"Local: {urls['local']}")
    print(f"LAN:   {urls['lan']}")
    print("==============================")
    print()

    return server, urls

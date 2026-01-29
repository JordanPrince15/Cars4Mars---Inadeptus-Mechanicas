import tkinter as tk
from PIL import Image, ImageTk
import cv2
import threading

from JebsEyes.robot_state import RobotState
from JebsEyes.test_main import vision_loop
from JebsEyes.ui.panda_panel import PandaApp


class RoverUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rover Mission Control")
        self.root.geometry("1000x700")
        self.root.configure(bg="lightgray")

        # Shared state
        self.state = RobotState()
        self.stop_event = threading.Event()

        # Start vision thread
        self.vision_thread = threading.Thread(
            target=vision_loop,
            args=(self.state, self.stop_event),
            daemon=True
        )
        self.vision_thread.start()

            # --- LEFT PANEL (Video) ---
        left_frame = tk.Frame(root, bg="white")
        left_frame.pack(side="left", fill="both", expand=True)

        self.video_label = tk.Label(left_frame, bg="black")
        self.video_label.pack(padx=20, pady=20)

        self.status = tk.Label(
            left_frame,
            text="WiFi: ● Connected | Battery: 100% | Telemetry: OK",
            font=("Arial", 12),
            bg="white"
        )
        self.status.pack()

         # --- RIGHT PANEL (Panda3D) ---
        panda_frame = tk.Frame(root, width=400, bg="black")
        panda_frame.pack(side="right", fill="y")

        # Initialize Panda3D inside the frame
        self.panda = PandaApp(panda_frame.winfo_id(), root)


        # Start UI update loop
        self.update_ui()

        # Clean shutdown
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_ui(self):
        with self.state.lock:
            frame = self.state.frame
            # ball = self.state.ball
            detected_ball = self.state.ball_detected
            x = self.state.ball_x
            y = self.state.ball_y
            confidence = self.state.ball_confidence
            ball = None
            if detected_ball:
                ball = {
                    "x": x,
                    "y": y,
                    "size": 20,
                    "confidence": confidence
                }  

                px = (x - 320/2) / 10
                py = (y - 240/2) / 10
                self.panda.sim.set_ball_position(px, py, 0.5)
            else:
                self.panda.sim.ball_node.hide() # Hide ball if not detected

        if frame is not None:
            # Draw overlay (UI-side, not vision-side)
            display = frame.copy()

            if ball:
                cv2.circle(
                    display,
                    (ball["x"], ball["y"]),
                    ball["size"],
                    (0, 255, 0),
                    2
                )
                cv2.putText(
                    display,
                    f"Tennis Ball {ball['confidence']:.2f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )

            # Convert to Tkinter image
            rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        # Schedule next update
        self.root.after(15, self.update_ui)

    def on_close(self):
        self.stop_event.set()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = RoverUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

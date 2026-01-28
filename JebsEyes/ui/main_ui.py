# # import tkinter as tk
# # from panda_panel import PandaApp

# # def main():
# #     root = tk.Tk()
# #     root.title("Rover Mission Control")
# #     root.geometry("1200x700")
# #     root.configure(bg="white")

# #     # Left: video / UI placeholder
# #     left_frame = tk.Frame(root, width=800, height=700, bg="white")
# #     left_frame.pack(side="left", fill="both", expand=True)

# #     status = tk.Label(
# #         left_frame,
# #         text="WiFi: ● Connected | Battery: 100% | Telemetry: OK",
# #         font=("Arial", 12),
# #         bg="white"
# #     )
# #     status.pack(pady=10)

# #     video_placeholder = tk.Label(
# #         left_frame,
# #         text="VIDEO FEED",
# #         bg="#eaeaea",
# #         width=80,
# #         height=25
# #     )
# #     video_placeholder.pack(padx=20, pady=20)

# #     # Right: Panda3D panel
# #     panda_frame = tk.Frame(root, width=400, height=700, bg="black")
# #     panda_frame.pack(side="right", fill="y")

# #     root.update()  # ensure winfo_id exists

# #     panda = PandaApp(panda_frame.winfo_id())

# #     root.mainloop()


# # if __name__ == "__main__":
# #     main()

# import tkinter as tk
# from panda_panel import PandaApp

# def main():
#     root = tk.Tk()
#     root.title("Rover Mission Control")
#     root.geometry("1200x700")
#     root.configure(bg="white")

#     # LEFT PANEL (video + status)
#     left_frame = tk.Frame(root, bg="white")
#     left_frame.pack(side="left", fill="both", expand=True)

#     status = tk.Label(
#         left_frame,
#         text="WiFi: ● Connected | Battery: 100% | Telemetry: OK",
#         font=("Arial", 12),
#         bg="white"
#     )
#     status.pack(pady=10)

#     video_placeholder = tk.Label(
#         left_frame,
#         text="VIDEO FEED",
#         bg="#5b4d4d",
#         width=80,
#         height=25
#     )
#     video_placeholder.pack(padx=20, pady=20)

#     # RIGHT PANEL (Panda3D)
#     panda_frame = tk.Frame(root, width=400, bg="black")
#     panda_frame.pack(side="right", fill="y")

#     root.update()  # IMPORTANT: ensures winfo_id exists

#     PandaApp(panda_frame.winfo_id(), root)

#     root.mainloop()

# if __name__ == "__main__":
#     main()

import tkinter as tk
from PIL import Image, ImageTk
import cv2
import threading

from JebsEyes.robot_state import RobotState
from JebsEyes.test_main import vision_loop


class RoverUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rover Mission Control")
        self.root.geometry("1000x700")
        self.root.configure(bg="white")

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

        # --- UI Layout ---
        self.video_label = tk.Label(root, bg="black")
        self.video_label.pack(padx=20, pady=20)

        self.status = tk.Label(
            root,
            text="WiFi: ● Connected | Battery: 100% | Telemetry: OK",
            font=("Arial", 12),
            bg="white"
        )
        self.status.pack()

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

import tkinter as tk
import webbrowser
import threading

from JebsEyes.robot_state import RobotState
from JebsEyes.main import CAPTURE_DIR, CameraManager, vision_loop
from JebsEyes.ui.panda_panel import PandaApp
from JebsEyes.ui.web_viewer import AnnotatedFrameBroker, start_web_viewer
from JebsEyes.mission_controller import MissionController


class RoverUI:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Rover Mission Control"
        )

        self.root.geometry(
            "1000x700"
        )

        self.root.configure(
            bg="lightgray"
        )

        # ====================================================
        # SHARED STATE
        # ====================================================

        self.state = RobotState()

        self.stop_event = threading.Event()

        # ====================================================
        # MISSION CONTROLLER
        # ====================================================

        self.mission_controller = MissionController(
            self.state
        )

        # ====================================================
        # CAMERA
        # ====================================================

        self.camera = CameraManager()

        # ====================================================
        # ANNOTATED WEB FEED
        # ====================================================

        self.frame_broker = AnnotatedFrameBroker(
            CAPTURE_DIR
        )

        self.web_server, self.viewer_urls = start_web_viewer(
            self.frame_broker,
            self.state,
            self.camera,
            self.mission_controller
        )

        self.root.after(
            800,
            lambda: webbrowser.open(
                self.viewer_urls["local"]
            )
        )

        # ====================================================
        # VISION THREAD
        # ====================================================

        self.vision_thread = threading.Thread(
            target=vision_loop,
            args=(
                self.state,
                self.stop_event,
                self.camera,
                self.mission_controller,
                self.frame_broker
            ),
            daemon=True
        )

        self.vision_thread.start()

        # ====================================================
        # MISSION CONTROL UI
        # ====================================================
        
        self.control_frame = tk.LabelFrame(
            self.root,
            text="Mission Control",
            padx=10,
            pady=10
        )
        
        self.control_frame.pack(
            side=tk.TOP,
            fill=tk.X,
            padx=20,
            pady=10
        )
        
        # ====================================================
        # CONTROL MODE BUTTONS
        # ====================================================
        
        # ----------------------------------------------------
        # MANUAL
        # ----------------------------------------------------
        
        self.manual_button = tk.Button(
            self.control_frame,
            text="MANUAL",
            width=15,
            command=lambda:
                self.set_control_mode("MANUAL")
        )
        
        self.manual_button.pack(
            side=tk.LEFT,
            padx=5
        )
        
        # ----------------------------------------------------
        # AUTONOMOUS
        # ----------------------------------------------------
        
        self.autonomous_button = tk.Button(
            self.control_frame,
            text="AUTONOMOUS",
            width=15,
            command=lambda:
                self.set_control_mode("AUTONOMOUS")
        )
        
        self.autonomous_button.pack(
            side=tk.LEFT,
            padx=5
        )
        
        # ====================================================
        # MISSION BUTTONS
        # ====================================================
        
        # ----------------------------------------------------
        # OBJECTS
        # ----------------------------------------------------
        
        self.objects_button = tk.Button(
            self.control_frame,
            text="OBJECTS",
            width=15,
            command=lambda:
                self.set_mission("OBJECTS")
        )
        
        self.objects_button.pack(
            side=tk.LEFT,
            padx=5
        )
        
        # ----------------------------------------------------
        # BALLOONS
        # ----------------------------------------------------
        
        self.balloons_button = tk.Button(
            self.control_frame,
            text="BALLOONS",
            width=15,
            command=lambda:
                self.set_mission("BALLOONS")
        )
        
        self.balloons_button.pack(
            side=tk.LEFT,
            padx=5
        )
        
        # ====================================================
        # MISSION STATUS
        # ====================================================
        
        self.mission_status = tk.Label(
            self.control_frame,
            text="MODE: MANUAL",
            font=("Arial", 12, "bold")
        )
        
        self.mission_status.pack(
            side=tk.LEFT,
            padx=20
        )

        self.update_mission_controls()

        # ====================================================
        # LEFT PANEL (VIDEO)
        # ====================================================

        left_frame = tk.Frame(
            self.root,
            bg="white"
        )

        left_frame.pack(
            side="left",
            fill="both",
            expand=True
        )

        # ----------------------------------------------------
        # Web feed status
        #
        # The annotated FPV view now lives in the browser
        # so this window does not get captured and re-drawn.
        # ----------------------------------------------------

        self.video_label = tk.Label(
            left_frame,
            text=(
                "Annotated FPV feed is in the browser.\n"
                f"{self.viewer_urls['local']}\n"
                f"{self.viewer_urls['lan']}"
            ),
            font=("Arial", 14),
            bg="black",
            fg="white",
            justify="center"
        )

        self.video_label.pack(
            padx=20,
            pady=20,
            fill="both",
            expand=True
        )

        self.open_feed_button = tk.Button(
            left_frame,
            text="Open annotated feed",
            command=lambda: webbrowser.open(
                self.viewer_urls["local"]
            )
        )

        self.open_feed_button.pack(
            pady=5
        )

        # ----------------------------------------------------
        # Temporary direction label
        # ----------------------------------------------------

        Direction = tk.Label(
            left_frame,
            text="This is a simple label",
            font=("Arial", 24),
            bg="white"
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self.status = tk.Label(
            left_frame,
            text=(
                "WiFi: ● Connected | "
                "Battery: 100% | "
                "Telemetry: OK "
                + Direction.cget("text")
            ),
            font=("Arial", 12),
            bg="white"
        )

        self.status.pack()

        # ====================================================
        # RIGHT PANEL (PANDA3D)
        # ====================================================

        panda_frame = tk.Frame(
            self.root,
            width=400,
            bg="black"
        )

        panda_frame.pack(
            side="right",
            fill="y"
        )

        # ----------------------------------------------------
        # Initialize Panda3D
        # ----------------------------------------------------

        self.panda = PandaApp(
            panda_frame.winfo_id(),
            self.root
        )

        
        # ====================================================
        # INITIALISE MISSION CONTROLS
        # ====================================================


        # ====================================================
        # CLEAN SHUTDOWN
        # ====================================================

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        # ====================================================
        # START UI UPDATE LOOP
        # ====================================================

        self.update_ui()

    # ========================================================
    # SET CONTROL MODE
    # ========================================================

    def set_control_mode(self, mode):
        """
        Change between MANUAL and AUTONOMOUS control.
        """

        self.mission_controller.set_control_mode(
            mode
        )

        self.update_mission_controls()

    # ========================================================
    # SET MISSION
    # ========================================================

    def set_mission(self, mission):
        """
        Change the active autonomous mission.
        """

        self.mission_controller.set_mission(
            mission
        )

        self.update_mission_controls()

    # ========================================================
    # UPDATE MISSION CONTROLS
    # ========================================================

    def update_mission_controls(self):
        """
        Update mission-control buttons and
        status display.
        """

        # ----------------------------------------------------
        # Read current state
        # ----------------------------------------------------

        with self.state.lock:

            control_mode = (
                self.state.control_mode
            )

            mission = (
                self.state.mission
            )

        # ====================================================
        # STATUS TEXT
        # ====================================================

        if control_mode == "MANUAL":

            self.mission_status.config(
                text="MODE: MANUAL"
            )

        else:

            self.mission_status.config(
                text=(
                    f"MODE: AUTONOMOUS | "
                    f"{mission}"
                )
            )

        # ====================================================
        # MISSION BUTTONS
        # ====================================================

        if control_mode == "AUTONOMOUS":

            self.objects_button.config(
                state=tk.NORMAL
            )

            self.balloons_button.config(
                state=tk.NORMAL
            )

        else:

            self.objects_button.config(
                state=tk.DISABLED
            )

            self.balloons_button.config(
                state=tk.DISABLED
            )

    # ========================================================
    # UPDATE UI
    # ========================================================

    def update_ui(self):

        # # ----------------------------------------------------
        # # Update mission controls
        # # ----------------------------------------------------

        # self.update_mission_controls()

        # ====================================================
        # READ SHARED STATE
        # ====================================================

        with self.state.lock:

            detected_ball = (
                self.state.ball_detected
            )

            x = self.state.ball_x
            y = self.state.ball_y

            control_mode = self.state.control_mode
            mission = self.state.mission

        last_archive = self.frame_broker.last_archive_name

        self.video_label.config(
            text=(
                "Annotated FPV feed is in the browser.\n"
                f"{self.viewer_urls['local']}\n"
                f"{self.viewer_urls['lan']}\n\n"
                f"MODE: {control_mode} | {mission}\n"
                + (
                    f"Last screenshot: {last_archive}"
                    if last_archive
                    else "Waiting for first annotated frame..."
                )
            )
        )

        # ====================================================
        # UPDATE 3D VIEW
        # ====================================================

        if detected_ball:

            px = (
                x - 320 / 2
            ) / 10

            py = (
                y - 240 / 2
            ) / 10

            self.panda.sim.set_ball_position(
                px,
                py,
                0.5
            )

            # ------------------------------------------------
            # Sync robot head with real stepper angle
            # ------------------------------------------------

            # self.panda.sim.set_sensor_angle(
            #     self.current_pan
            # )

        else:

            self.panda.sim.ball_node.hide()

        # ====================================================
        # RUN AGAIN
        # ====================================================

        self.root.after(
            250,
            self.update_ui
        )

    # ========================================================
    # CLEAN SHUTDOWN
    # ========================================================

    def on_close(self):
        """
        Cleanly shut down the application.
        """

        print(
            "Shutting down Jeb..."
        )

        # ----------------------------------------------------
        # Stop vision thread
        # ----------------------------------------------------

        self.stop_event.set()

        # ----------------------------------------------------
        # Stop robot and close controller
        # ----------------------------------------------------

        self.mission_controller.close()

        # ----------------------------------------------------
        # Close UI
        # ----------------------------------------------------

        self.root.destroy()


# ============================================================
# MAIN
# ============================================================

def main():

    root = tk.Tk()

    app = RoverUI(
        root
    )

    root.mainloop()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
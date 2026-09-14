
# ============================================================
# BALLOON MISSION
# ============================================================

import time

from JebsEyes.balloon_decector import BalloonDetector


class BalloonMission:
    """
    Handles the balloon mission.

    Current functionality:
        - Detect balloons
        - Seek for the current target
        - Track the current target
        - Send movement commands

    Current mission order:
        black → white → pink → yellow → blue

    Not implemented yet:
        - Ultrasonic distance
        - 1.5 m stopping
        - 5 second wait
        - Automatic next-target transition
        - Panoramic seeking
    """

    # --------------------------------------------------------
    # MISSION ORDER
    # --------------------------------------------------------

    MISSION = [
        "black_balloon",
        "white_balloon",
        "pink_balloon",
        "yellow_balloon",
        "blue_balloon"
    ]

    # --------------------------------------------------------
    # INITIALIZATION
    # --------------------------------------------------------

    def __init__(self, robot_controller):

        self.current_index = 0
        self.target = self.MISSION[self.current_index]

        # Mission state
        self.state = "SEEKING"

        # Whether the current target has been detected
        self.target_acquired = False

        # Robot controller
        self.robot = robot_controller

        # Movement command timing
        self.last_command_time = 0.0
        self.command_interval = 0.2

        print()
        print("================================")
        print("       BALLOON MISSION")
        print("================================")
        print(f"CURRENT TARGET: {self.target.upper()}")
        print(f"STATE:          {self.state}")
        print("================================")

        print("Initializing balloon mission...")

        self.detector = BalloonDetector()

        print("✓ Balloon mission initialized.")

    # --------------------------------------------------------
    # PROCESS FRAME
    # --------------------------------------------------------

    def process_frame(self, frame):
        """
        Detect balloons in the current frame.

        This performs the Roboflow inference once.

        The resulting detections are returned to the
        MissionController, which can then pass them to
        the mission logic.
        """

        print("[Balloon mission]: processing frame...")

        detections = self.detector.detect(frame)

        print(
            f"[BALLOON MISSION] "
            f"Detections: {detections}"
        )

        return {
            "mission": "BALLOONS",
            "detections": detections,
            "action": None
        }

    # --------------------------------------------------------
    # CURRENT TARGET
    # --------------------------------------------------------

    def get_target(self):
        """Return the balloon Jeb is currently looking for."""

        return self.target

    # --------------------------------------------------------
    # SEEK
    # --------------------------------------------------------

    def seek(self, detections):
        """
        Seek for the current target.

        For now, seeking simply means:

            Look at the current camera frame
            ↓
            Check whether the target balloon exists

        Panoramic-image seeking will be added later.
        """

        target = self.process_detections(detections)

        if target is None:

            self.state = "SEEKING"

            return None

        # Target found
        self.target_acquired = True
        self.state = "TRACKING"

        print()
        print("================================")
        print("       TARGET FOUND")
        print("================================")
        print(f"TARGET: {self.target.upper()}")
        print("STATE:  TRACKING")
        print("================================")

        return target

    # --------------------------------------------------------
    # PROCESS DETECTIONS
    # --------------------------------------------------------

    def process_detections(self, detections):
        """
        Process the detections returned by BalloonDetector.

        Only detections matching the current target are used.
        """

        if not detections:

            self.target_acquired = False

            return None

        # Find detections matching the current target
        matching = [
            detection
            for detection in detections
            if detection["class"] == self.target
        ]

        # Target not found
        if not matching:

            self.target_acquired = False

            detected_names = [
                detection["class"]
                for detection in detections
            ]

            print(
                f"[BALLOON MISSION] "
                f"TARGET: {self.target.upper()} | "
                f"Detected: {detected_names} | "
                f"→ Ignoring"
            )

            return None

        # Select the highest-confidence target
        best = max(
            matching,
            key=lambda detection: detection["confidence"]
        )

        self.target_acquired = True

        print()
        print("--------------------------------")
        print("✓ TARGET ACQUIRED")
        print("--------------------------------")

        print(
            f"TARGET:      "
            f"{best['class'].upper()}"
        )

        print(
            f"CONFIDENCE:  "
            f"{best['confidence'] * 100:.1f}%"
        )

        print(
            f"CENTER:      "
            f"({best['x']:.0f}, "
            f"{best['y']:.0f})"
        )

        print(
            f"SIZE:        "
            f"{best['width']:.0f} × "
            f"{best['height']:.0f}"
        )

        print("--------------------------------")

        return best

    # --------------------------------------------------------
    # TRACK
    # --------------------------------------------------------

    def track(self, frame, detections):
        """
        Track the current target.

        The detections are supplied by process_frame(), so
        Roboflow inference only happens once per frame.

        Commands:

            T L
                Turn left

            T R
                Turn right

            D 50
                Drive forward

        Commands are sent at most once every 0.2 seconds.
        """

        now = time.monotonic()

        # Prevent commands from being sent too quickly
        if (
            now - self.last_command_time
            < self.command_interval
        ):
            return None

        # Find the current target
        target = self.process_detections(detections)

        # Target disappeared
        if target is None:

            self.target_acquired = False
            self.state = "SEEKING"

            print(
                "[BALLOON TRACKING] "
                "Target lost → SEEKING"
            )

            return None

        # Target is visible
        self.target_acquired = True
        self.state = "TRACKING"

        # ----------------------------------------------------
        # FIND IMAGE CENTRE
        # ----------------------------------------------------

        frame_width = frame.shape[1]

        frame_center = frame_width / 2

        balloon_x = target["x"]

        # Positive = balloon is to the right
        # Negative = balloon is to the left
        error = balloon_x - frame_center

        # ----------------------------------------------------
        # DEADZONE
        # ----------------------------------------------------

        deadzone = 50

        # ----------------------------------------------------
        # MOVEMENT DECISION
        # ----------------------------------------------------

        if error < -deadzone:

            # Balloon is to the left
            command = "T L"

        elif error > deadzone:

            # Balloon is to the right
            command = "T R"

        else:

            # Balloon is approximately centred
            command = "D 50"

        # ----------------------------------------------------
        # SEND COMMAND
        # ----------------------------------------------------

        success = self.robot.makeMovementCommand(command)

        self.last_command_time = now

        print(
            f"[BALLOON TRACKING] "
            f"X={balloon_x:.0f} | "
            f"CENTER={frame_center:.0f} | "
            f"ERROR={error:.0f} | "
            f"COMMAND={command}"
        )

        return command

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    def update(self, frame, detections):
        """
        Main balloon-mission update function.

        SEEKING:
            Look for the current target.

        TRACKING:
            Follow the target.

        Returns the movement command, if one was issued.
        """

        if self.state == "SEEKING":

            self.seek(detections)

            return None

        if self.state == "TRACKING":

            return self.track(
                frame,
                detections
            )

        return None

    # --------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------

    def close(self):
        """Nothing to close yet."""

        pass

    # --------------------------------------------------------
    # ADVANCE TO NEXT BALLOON
    # --------------------------------------------------------

    def next_target(self):
        """
        Move to the next balloon.

        Automatic calling of this function will be added
        once distance detection and the 5-second stop
        requirement are implemented.
        """

        if self.current_index >= len(self.MISSION) - 1:

            print()
            print("================================")
            print("       MISSION COMPLETE")
            print("================================")

            self.state = "COMPLETE"

            return False

        self.current_index += 1

        self.target = self.MISSION[
            self.current_index
        ]

        self.target_acquired = False

        self.state = "SEEKING"

        print()
        print("================================")
        print("         NEXT BALLOON")
        print("================================")
        print(
            f"CURRENT TARGET: "
            f"{self.target.upper()}"
        )
        print("STATE: SEEKING")
        print("================================")

        return True

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    def is_complete(self):
        """Return True when all five balloons are complete."""

        return (
            self.current_index
            >= len(self.MISSION) - 1
        )


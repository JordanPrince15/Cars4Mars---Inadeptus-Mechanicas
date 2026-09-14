
# ============================================================
# BALLOON MISSION
# ============================================================

class BalloonMission:

    # Mission order
    MISSION = [
        "black_balloon",
        "white_balloon",
        "pink_balloon",
        "yellow_balloon",
        "blue_balloon"
    ]

    def __init__(self):

        self.current_index = 0
        self.target = self.MISSION[self.current_index]

        self.target_acquired = False

        print()
        print("================================")
        print("       BALLOON MISSION")
        print("================================")
        print(f"CURRENT TARGET: {self.target.upper()}")
        print("================================")

    # --------------------------------------------------------
    # CURRENT TARGET
    # --------------------------------------------------------

    def get_target(self):
        """Return the balloon Jeb is currently looking for."""

        return self.target

    # --------------------------------------------------------
    # PROCESS DETECTIONS
    # --------------------------------------------------------

    def process_detections(self, detections):
        """
        Process the clean detections returned by BalloonDetector.

        For now this ONLY identifies the target.

        No motor commands are made here yet.
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

        # ----------------------------------------------------
        # Target not found
        # ----------------------------------------------------

        if not matching:

            self.target_acquired = False

            detected_names = [
                detection["class"]
                for detection in detections
            ]

            print(
                f"TARGET: {self.target.upper()} | "
                f"Detected: {detected_names} | "
                f"→ Ignoring"
            )

            return None

        # ----------------------------------------------------
        # Target found
        # ----------------------------------------------------

        best = max(
            matching,
            key=lambda detection: detection["confidence"]
        )

        self.target_acquired = True

        print()
        print("--------------------------------")
        print("✓ TARGET ACQUIRED")
        print("--------------------------------")
        print(f"TARGET:      {best['class'].upper()}")
        print(f"CONFIDENCE:  {best['confidence'] * 100:.1f}%")
        print(
            f"CENTER:      "
            f"({best['x']:.0f}, {best['y']:.0f})"
        )
        print(
            f"SIZE:        "
            f"{best['width']:.0f} × "
            f"{best['height']:.0f}"
        )
        print("--------------------------------")

        return best

    # --------------------------------------------------------
    # ADVANCE TO NEXT BALLOON
    # --------------------------------------------------------

    def next_target(self):
        """
        Move to the next balloon in the mission.

        This will eventually be called after Jeb has:
        1. Reached the balloon
        2. Stopped within 1.5 m
        3. Remained stopped for 5 seconds
        """

        if self.current_index >= len(self.MISSION) - 1:

            print()
            print("================================")
            print("       MISSION COMPLETE")
            print("================================")

            return False

        self.current_index += 1
        self.target = self.MISSION[self.current_index]

        self.target_acquired = False

        print()
        print("================================")
        print("       NEXT BALLOON")
        print("================================")
        print(f"CURRENT TARGET: {self.target.upper()}")
        print("================================")

        return True

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    def is_complete(self):
        """Return True when all five balloons are complete."""

        return self.current_index >= len(self.MISSION) - 1


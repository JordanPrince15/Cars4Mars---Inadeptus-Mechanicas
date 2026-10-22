from JebsEyes.object_mission import ObjectMission
from JebsEyes.robot_controller import RobotController
from JebsEyes.balloon_mission import BalloonMission


class MissionController:
    """
    Central controller for Jeb's operating modes and missions.

    Valid control modes:
        MANUAL
        AUTONOMOUS

    Valid autonomous missions:
        OBJECTS
        BALLOONS

    Currently only the OBJECTS mission is implemented.
    """

    # =====================================================
    # VALID MODES
    # =====================================================

    MANUAL = "MANUAL"
    AUTONOMOUS = "AUTONOMOUS"

    OBJECTS = "OBJECTS"
    BALLOONS = "BALLOONS"

    def __init__(self, state):
        self.state = state

        # -------------------------------------------------
        # Robot hardware controller
        # -------------------------------------------------

        self.robot = RobotController(
            port="COM7",
            baudrate=115200
        )

        # -------------------------------------------------
        # Missions
        # -------------------------------------------------

        self.object_mission = ObjectMission()
        self.balloon_mission = BalloonMission(self.robot)

        # -------------------------------------------------
        # Current operating state
        # -------------------------------------------------

        self.control_mode = self.MANUAL # For now, this is how we will be toggling between manual and autonomous control. This will be changed to a GUI button later.
        self.mission = self.OBJECTS

        # Keep RobotState synchronized.
        with self.state.lock:
            self.state.control_mode = self.control_mode
            self.state.mission = self.mission

        print()
        print("==============================")
        print("    MISSION CONTROLLER")
        print("==============================")
        print(f"Control mode: {self.control_mode}")
        print(f"Mission:      {self.mission}")
        print("==============================")
        print()

    # =====================================================
    # CONTROL MODE
    # =====================================================

    def set_control_mode(self, mode):
        """
        Change between MANUAL and AUTONOMOUS control.
        """

        mode = mode.upper()

        if mode not in (
            self.MANUAL,
            self.AUTONOMOUS
        ):
            raise ValueError(
                f"Invalid control mode: {mode}"
            )

        self.control_mode = mode

        with self.state.lock:
            self.state.control_mode = mode

        print(
            f"[MISSION CONTROLLER] "
            f"Control mode → {mode}"
        )

        # -------------------------------------------------
        # Manual mode
        #
        # Autonomous missions should not continue
        # commanding the robot when manual mode is selected.
        # -------------------------------------------------

        if mode == self.MANUAL:
            self.stop_robot()

    # =====================================================
    # MISSION
    # =====================================================

    def set_mission(self, mission):
        """
        Change the autonomous mission.

        Mission selection is only meaningful while
        operating autonomously.
        """

        mission = mission.upper()

        if mission not in (
            self.OBJECTS,
            self.BALLOONS
        ):
            raise ValueError(
                f"Invalid mission: {mission}"
            )
        # Stop whatever the previous mission was doing
        if mission != self.mission:
            self.stop_robot()


        self.mission = mission

        with self.state.lock:
            self.state.mission = mission

        print(
            f"[MISSION CONTROLLER] "
            f"Mission → {mission}"
        )

    # =====================================================
    # PROCESS FRAME
    # =====================================================

    def process_frame(self, frame):
        """
        Send the current camera frame to the active mission.

        Returns the mission result.
        """
        #-------------------------------------------------
        # Read current operating state
        #-------------------------------------------------

        with self.state.lock:
            control_mode = self.state.control_mode
            mission = self.state.mission


        # -------------------------------------------------
        # OBJECTS
        #
        # Detection and on-frame annotation always run so
        # the FPV / screen viewer stays labelled.
        # Robot commands are only sent in AUTONOMOUS.
        # -------------------------------------------------

        if mission == self.OBJECTS:

            result = self.object_mission.process_frame(
                frame
            )

            action = result["action"]

            if (
                control_mode == self.AUTONOMOUS
                and action in ("LEFT", "RIGHT")
            ):

                self.robot.send_command(action)

            return result

        # -------------------------------------------------
        # BALLOONS
        # -------------------------------------------------

        if mission == self.BALLOONS:

            result = self.balloon_mission.process_frame(frame)

            detections = result["detections"]
            action = None

            if control_mode == self.AUTONOMOUS:

                action = self.balloon_mission.update(
                    frame,
                    detections
                )

            result["action"] = action

            return result

        return {
            "mission": None,
            "action": None
        }


    # =====================================================
    # STOP ROBOT
    # =====================================================

    def stop_robot(self):
        """
        Stop autonomous movement.

        The exact STOP behaviour can be adapted to the
        Pico firmware later.
        """

        self.robot.send_command("STOP")

    # =====================================================
    # SHUTDOWN
    # =====================================================

    def close(self):
        """Cleanly shut down the robot controller."""

        self.stop_robot()
        self.robot.close()
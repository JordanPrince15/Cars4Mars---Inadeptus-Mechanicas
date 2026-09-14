import serial


class RobotController:
    """
    Handles communication between Jeb's computer and
    the Raspberry Pi Pico.

    The mission system tells this class WHAT command to send.
    This class handles HOW that command gets sent.
    """

    def __init__(self, port="COM7", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.pico = None

        self.connect()

    # =====================================================
    # CONNECTION
    # =====================================================

    def connect(self):
        """Attempt to connect to the Raspberry Pi Pico."""

        try:
            self.pico = serial.Serial(
                self.port,
                self.baudrate
            )

            print(
                f"✅ Connected to Pico on {self.port}"
            )

        except Exception as e:
            print(
                f"❌ Failed to connect to Pico: {e}"
            )

            self.pico = None

    # =====================================================
    # SEND COMMAND
    # =====================================================
    def makeMovementCommand(self, command):
        """
        Send a movement command to the Pico.

        Supported commands:
            D [speed]  -> drive forward/backward
            T L        -> turn left
            T R        -> turn right
        """

        if self.pico is None:
            print(f"[MOCK PICO] Movement command: {command}")
            return False

        try:
            message = f"{command}\n"
            self.pico.write(message.encode())
            self.pico.flush()

            print(f"[PICO] Sent: {command}")
            return True

        except Exception as e:
            print(f"❌ Failed to send movement command: {e}")
            self.pico = None
            return False
    # def send_command(self, command):
    #     """
    #     Send a command to the Pico.

    #     If the Pico is unavailable, use the mock output
    #     instead of crashing the program.
    #     """

    #     # -------------------------------------------------
    #     # Pico unavailable
    #     # -------------------------------------------------

    #     if self.pico is None:
    #         print(
    #             f"[PICO] Action: {command}"
    #         )
    #         return False

    #     # -------------------------------------------------
    #     # Pico available
    #     # -------------------------------------------------

    #     try:

    #         message = f"{command}\n"

    #         self.pico.write(
    #             message.encode()
    #         )

    #         self.pico.flush()

    #         return True

    #     except Exception as e:

    #         print(
    #             f"❌ Pico connection lost during runtime: {e}"
    #         )

    #         self.pico = None

    #         return False

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):
        """Close the Pico serial connection."""

        if self.pico is not None:

            try:
                self.pico.close()

            except Exception:
                pass

            self.pico = None
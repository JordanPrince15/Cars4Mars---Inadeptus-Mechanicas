from panda3d.core import WindowProperties, loadPrcFileData
from direct.showbase.ShowBase import ShowBase
from JebsEyes.panda.robot_simulator import RobotSimulator

# Prevent Panda from opening its own window
loadPrcFileData("", "window-type none")

class PandaApp(ShowBase):
    def __init__(self, parent_window_id, tk_root):
        ShowBase.__init__(self)

        # Embed Panda3D inside Tkinter
        wp = WindowProperties()
        wp.setParentWindow(parent_window_id)
        wp.setOrigin(0, 0)
        wp.setSize(400, 700)
        self.makeDefaultPipe()
        self.openDefaultWindow(props=wp)

        self.setBackgroundColor(0.95, 0.95, 0.95, 1)

        # Robot simulator
        self.sim = RobotSimulator(self)

        # Tkinter root reference
        self.tk_root = tk_root

        # Run Panda3D "step" inside Tkinter mainloop
        self._step()

    def _step(self):
        """Step Panda3D task in main thread."""
        self.taskMgr.step()
        self.tk_root.after(10, self._step)

